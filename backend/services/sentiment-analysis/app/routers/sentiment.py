"""
API router — exposes scraping trigger, daily scores, article listing,
and markdown report generation.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Article, async_session_factory, get_session
from app.services.aggregator import compute_daily_scores, get_today_scores
from app.services.llm import analyze_sentiment
from app.services.scraper import scrape_all_sources
from app.services.perplexity_search import search_social_media_for_ticker, search_social_media_batch

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sentiment"])

# ── Company name ↔ ticker mapping ───────────────────────

COMPANY_TO_TICKER: dict[str, str] = {
    "sfbt": "SFBT",
    "société frigorifique et brasserie de tunis": "SFBT",
    "biat": "BIAT",
    "banque internationale arabe de tunisie": "BIAT",
    "bna": "BNA",
    "banque nationale agricole": "BNA",
    "sah": "SAH",
    "société d'articles hygiéniques": "SAH",
    "carthage": "CARTHAGE",
    "ciments de carthage": "CARTHAGE",
    "poulina": "POULINA",
    "poulina group holding": "POULINA",
    "poulina group": "POULINA",
    "delice": "DELICE",
    "délice holding": "DELICE",
    "délice": "DELICE",
    "euro-cycles": "EURO-CYCLES",
    "eurocycles": "EURO-CYCLES",
    "euro cycles": "EURO-CYCLES",
    "telnet": "TELNET",
    "telnet holding": "TELNET",
    "tunisair": "TUNISAIR",
}


def _resolve_ticker(company: str) -> str | None:
    """Resolve a company name or ticker symbol to the canonical ticker."""
    key = company.strip().lower()
    if key in COMPANY_TO_TICKER:
        return COMPANY_TO_TICKER[key]
    # Also try uppercase direct match against known tickers
    upper = company.strip().upper()
    from app.config import TICKERS
    if upper in TICKERS:
        return upper
    return None


# ── Background pipeline ────────────────────────────────


async def _scrape_and_analyse() -> None:
    """
    Full pipeline executed as a background task:
      1. Scrape all sources
      2. Deduplicate against DB
      3. Send each new article to the LLM
      4. Persist articles + sentiment
      5. Recompute daily aggregates
    """
    logger.info("🚀 Background scrape-and-analyse pipeline started")

    # 1 — Scrape
    scrape_result = await scrape_all_sources()
    raw_articles = scrape_result.articles
    if scrape_result.errors:
        for err in scrape_result.errors:
            logger.warning("Scraper error: %s", err)

    if not raw_articles:
        logger.warning("No articles scraped — nothing to analyse")
        return

    logger.info("Scraped %d raw articles total", len(raw_articles))

    # 2 — Deduplicate & persist + analyse
    async with async_session_factory() as session:
        new_count = 0
        for raw in raw_articles:
            # Check if title already exists (simple dedup)
            exists_stmt = select(Article.id).where(Article.title == raw.title).limit(1)
            exists = (await session.execute(exists_stmt)).scalar_one_or_none()
            if exists:
                continue

            # 3 — LLM sentiment analysis
            sentiment_res = await analyze_sentiment(
                title=raw.title,
                snippet=raw.content_snippet,
                language=raw.language,
            )

            # 4 — Save article with sentiment
            article = Article(
                source=raw.source,
                title=raw.title,
                url=raw.url,
                content_snippet=raw.content_snippet,
                language=raw.language,
                sentiment=sentiment_res.sentiment,
                score=sentiment_res.score,
                ticker=sentiment_res.ticker,
            )
            session.add(article)
            new_count += 1

        await session.commit()
        logger.info("Persisted %d new articles with sentiment", new_count)

        # 5 — Recompute daily aggregates
        await compute_daily_scores(session)

    logger.info("✅ Background pipeline finished")


# ── Endpoints ───────────────────────────────────────────


@router.post("/trigger-scrape", summary="Trigger scraping & analysis")
async def trigger_scrape(background_tasks: BackgroundTasks) -> dict[str, str]:
    """
    Manually kicks off the scraping + LLM analysis pipeline
    as a background task so the endpoint returns immediately.
    """
    background_tasks.add_task(_scrape_and_analyse)
    return {
        "status": "accepted",
        "message": "Scrape & analysis pipeline queued. Check /articles shortly.",
    }


@router.get("/sentiments/daily", summary="Today's aggregated sentiment scores")
async def daily_sentiments(
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """
    Returns the average sentiment score per ticker for today.
    """
    scores = await get_today_scores(session)

    return {
        "date": dt.datetime.utcnow().strftime("%Y-%m-%d"),
        "tickers": [
            {
                "ticker": s.ticker,
                "avg_score": s.avg_score,
                "article_count": s.article_count,
                "classification": "positive" if s.avg_score > 0.15 else ("negative" if s.avg_score < -0.15 else "neutral"),
            }
            for s in scores
        ],
    }


@router.get("/articles", summary="Latest analysed articles")
async def list_articles(
    limit: int = 50,
    source: str | None = None,
    ticker: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """
    Returns the most recent analysed articles.
    Optional filters: ``source`` (IlBoursa, Tustex, TunisieNumerique)
    and ``ticker`` (e.g. SFBT).
    """
    stmt = select(Article).order_by(Article.created_at.desc()).limit(limit)

    if source:
        stmt = stmt.where(Article.source == source)
    if ticker:
        stmt = stmt.where(Article.ticker == ticker.upper())

    rows = (await session.execute(stmt)).scalars().all()

    return {
        "count": len(rows),
        "articles": [
            {
                "id": a.id,
                "source": a.source,
                "title": a.title,
                "url": a.url,
                "language": a.language,
                "sentiment": a.sentiment,
                "score": a.score,
                "ticker": a.ticker,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in rows
        ],
    }


# ── Markdown report endpoint ───────────────────────────


def _sentiment_emoji(sentiment: str | None) -> str:
    return {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}.get(
        sentiment or "", "⚪"
    )


def _build_markdown(ticker: str, articles: list[Article]) -> str:
    """Generate a pretty markdown report for a company."""
    now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Compute aggregate stats
    scores = [a.score for a in articles if a.score is not None]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    pos = sum(1 for a in articles if a.sentiment == "positive")
    neg = sum(1 for a in articles if a.sentiment == "negative")
    neu = sum(1 for a in articles if a.sentiment == "neutral")

    overall = "positive" if avg_score > 0.15 else ("negative" if avg_score < -0.15 else "neutral")

    lines: list[str] = []
    lines.append(f"# 📊 Sentiment Report — {ticker}")
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total articles analysed | **{len(articles)}** |")
    lines.append(f"| Average sentiment score | **{avg_score:+.3f}** |")
    lines.append(f"| Overall sentiment | {_sentiment_emoji(overall)} **{overall.upper()}** |")
    lines.append(f"| 🟢 Positive articles | {pos} |")
    lines.append(f"| 🔴 Negative articles | {neg} |")
    lines.append(f"| 🟡 Neutral articles | {neu} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Articles Detail")
    lines.append("")

    for i, a in enumerate(articles, 1):
        emoji = _sentiment_emoji(a.sentiment)
        date_str = a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "N/A"
        lines.append(f"### {i}. {a.title}")
        lines.append("")
        lines.append(f"- **Source:** {a.source}")
        lines.append(f"- **Date:** {date_str}")
        lines.append(f"- **Language:** {a.language or 'N/A'}")
        if a.score is not None:
            lines.append(f"- **Sentiment:** {emoji} {a.sentiment or 'N/A'} ({a.score:+.2f})")
        else:
            lines.append(f"- **Sentiment:** {emoji} {a.sentiment or 'N/A'}")
        if a.url:
            lines.append(f"- **URL:** [{a.url}]({a.url})")
        else:
            lines.append("- **URL:** N/A")
        if a.content_snippet:
            snippet = a.content_snippet[:300].replace("\n", " ")
            lines.append(f"- **Snippet:** _{snippet}_")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_Report generated by BVMT Sentiment Analysis Module_")
    lines.append("")

    return "\n".join(lines)


@router.get(
    "/report/{company}",
    summary="Markdown sentiment report for a company",
    response_class=Response,
)
async def company_report(
    company: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """
    Given a company name or ticker (e.g. ``SFBT``, ``Poulina``,
    ``Banque Internationale Arabe de Tunisie``), return a downloadable
    **Markdown (.md) file** with a full sentiment report including:

    - Overall sentiment summary & average score
    - Breakdown of positive / negative / neutral articles
    - Per-article details (title, source, date, sentiment, score, snippet)
    """
    ticker = _resolve_ticker(company)
    if ticker is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown company '{company}'. "
                "Use a known ticker (SFBT, BIAT, BNA, SAH, CARTHAGE, POULINA, "
                "DELICE, EURO-CYCLES, TELNET, TUNISAIR) or full company name."
            ),
        )

    stmt = (
        select(Article)
        .where(Article.ticker == ticker)
        .order_by(Article.created_at.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No articles found for ticker '{ticker}'. Run /trigger-scrape first.",
        )

    md_content = _build_markdown(ticker, list(rows))
    filename = f"sentiment_report_{ticker}_{dt.datetime.utcnow().strftime('%Y%m%d')}.md"

    return Response(
        content=md_content,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# ── 🇹🇳 K.O. FEATURE: Tunizi Analysis Demo ──────────────────────────


@router.post("/analyze-tunizi", summary="🇹🇳 K.O. Feature: Analyze Tunizi text")
async def analyze_tunizi_text(text: str) -> dict[str, Any]:
    """
    **THE K.O. FEATURE** - Tunizi/Arabizi sentiment analysis.
    
    This endpoint demonstrates the competitive advantage:
    - Understands Tunisian dialect (Tunizi)
    - Normalizes Arabizi (3→aa, 7→h, 9→q)
    - Detects financial slang ("ti7"=drop, "tla3"=rise)
    - Maps nicknames to tickers ("la bière"→SFBT)
    - Combines Gemini + Tunizi scores (60% Tunizi weight)
    
    **Examples to try:**
    - "SFBT bech ti7 2main" → Bearish (will drop tomorrow)
    - "La bière tla3et behi" → Bullish (beer went up nicely)
    - "Poulina yaasr lyoum" → Bullish (Poulina great today)
    - "Grève SNCFT cata" → Bearish (strike catastrophe)
    """
    # Analyze with Gemini + Tunizi enhancement
    result = await analyze_sentiment(
        title=text,
        snippet=None,
        language="tn",  # Tunisian
        enable_tunizi=True,
    )
    
    return {
        "input_text": text,
        "sentiment": result.sentiment,
        "score": result.score,
        "ticker": result.ticker,
        "tunizi_analysis": result.tunizi_metadata if result.tunizi_metadata else {
            "message": "No Tunizi keywords detected"
        },
        "explanation": _generate_explanation(result),
    }


def _generate_explanation(result) -> str:
    """Generate human-readable explanation of the analysis."""
    if not result.tunizi_metadata:
        return f"Standard analysis: {result.sentiment.upper()} (score: {result.score:.2f})"
    
    meta = result.tunizi_metadata
    keywords = meta.get("tunizi_keywords", [])
    
    parts = [f"Analysis: {result.sentiment.upper()} (score: {result.score:.2f})"]
    
    if meta.get("enhancement_applied"):
        parts.append(
            f"✨ Tunizi enhancement applied: "
            f"Base score {meta['base_score']:.2f} → Enhanced {meta['combined_score']:.2f}"
        )
    
    if keywords:
        parts.append(f"🇹🇳 Tunizi keywords detected: {', '.join(keywords[:5])}")
    
    lang = meta.get("language_detection", {})
    if lang.get("tunizi_slang", 0) > 0:
        parts.append("🗣️ Tunisian dialect detected")
    if lang.get("arabizi", 0) > 0:
        parts.append("🔢 Arabizi normalization applied")
    
    return " | ".join(parts)


# ── 🐦 K.O. FEATURE: Social Media Search ──────────────────────────


@router.post("/search-social-media", summary="🐦 Search Twitter, Reddit, Facebook, Tunisia-Sat for ticker")
async def search_social_media(
    ticker: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """
    **THE K.O. FEATURE** - Social media sentiment scraping.
    
    This endpoint searches multiple social media platforms for discussions
    about a specific stock ticker using Perplexity's real-time search:
    
    **Platforms searched:**
    - 🐦 Twitter/X (Tunisian finance community)
    - 📱 Reddit r/tunisia (investment discussions)
    - 👥 Facebook (Tunisian finance groups)
    - 💬 tunisia-sat.com forums (BVMT discussions)
    
    **What makes this a K.O. feature:**
    - Captures retail investor sentiment (not just official news)
    - Real-time search using Perplexity Sonar
    - Understands Tunizi/Arabizi in social posts
    - Complements official sources (IlBoursa, Tustex)
    
    **Example:** `POST /search-social-media?ticker=SFBT`
    
    Returns:
    - Posts found on each platform
    - Sentiment analysis using Tunizi NLP
    - Average social sentiment score
    - Comparison with official news sentiment
    """
    ticker_upper = ticker.upper()
    
    logger.info(f"🔍 Searching social media for ticker: {ticker_upper}")
    
    # Search social media with Perplexity
    try:
        social_posts = await search_social_media_for_ticker(ticker_upper)
    except Exception as e:
        logger.error(f"❌ Perplexity search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Social media search failed: {str(e)}"
        )
    
    if not social_posts:
        return {
            "ticker": ticker_upper,
            "total_posts": 0,
            "platforms": {},
            "sentiment": None,
            "message": "No social media discussions found for this ticker in the past 7 days."
        }
    
    # Analyze each post with Tunizi NLP
    analyzed_posts = []
    for post in social_posts:
        try:
            # Extract first 100 chars as title, rest as snippet
            title = post.content[:100] if post.content else ""
            snippet = post.content[100:] if len(post.content) > 100 else ""
            
            sentiment_result = await analyze_sentiment(
                title=title,
                snippet=snippet if snippet else None,
                language="tn",  # Assume Tunisian for social media
                enable_tunizi=True,
            )
            
            analyzed_posts.append({
                "platform": post.platform,
                "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                "url": post.url if post.url else "N/A",
                "author": post.author if post.author else "N/A",
                "sentiment": sentiment_result.sentiment,
                "score": sentiment_result.score,
                "tunizi_detected": bool(sentiment_result.tunizi_metadata),
            })
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to analyze post: {e}")
            continue
    
    # Compute aggregate sentiment
    scores = [p["score"] for p in analyzed_posts]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    positive = sum(1 for p in analyzed_posts if p["sentiment"] == "positive")
    negative = sum(1 for p in analyzed_posts if p["sentiment"] == "negative")
    neutral = sum(1 for p in analyzed_posts if p["sentiment"] == "neutral")
    
    overall_sentiment = "positive" if avg_score > 0.15 else ("negative" if avg_score < -0.15 else "neutral")
    
    # Group by platform
    by_platform = {}
    for post in analyzed_posts:
        platform = post["platform"]
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(post)
    
    # Get official news sentiment for comparison
    stmt = (
        select(Article)
        .where(Article.ticker == ticker_upper)
        .where(Article.created_at >= dt.datetime.utcnow() - dt.timedelta(days=7))
    )
    news_articles = (await session.execute(stmt)).scalars().all()
    news_scores = [a.score for a in news_articles if a.score is not None]
    news_avg = sum(news_scores) / len(news_scores) if news_scores else None
    
    return {
        "ticker": ticker_upper,
        "total_posts": len(analyzed_posts),
        "platforms": {
            platform: {
                "count": len(posts),
                "posts": posts[:5],  # Limit to 5 posts per platform
            }
            for platform, posts in by_platform.items()
        },
        "sentiment_summary": {
            "overall_sentiment": overall_sentiment,
            "avg_score": round(avg_score, 3),
            "positive_posts": positive,
            "negative_posts": negative,
            "neutral_posts": neutral,
        },
        "comparison": {
            "social_media_sentiment": round(avg_score, 3),
            "official_news_sentiment": round(news_avg, 3) if news_avg is not None else None,
            "delta": round(avg_score - news_avg, 3) if news_avg is not None else None,
            "interpretation": _interpret_sentiment_gap(avg_score, news_avg) if news_avg is not None else None,
        },
        "tunizi_stats": {
            "posts_with_tunizi": sum(1 for p in analyzed_posts if p["tunizi_detected"]),
            "percentage": round(100 * sum(1 for p in analyzed_posts if p["tunizi_detected"]) / len(analyzed_posts), 1),
        }
    }


def _interpret_sentiment_gap(social_score: float, news_score: float) -> str:
    """Interpret the gap between social media and official news sentiment."""
    delta = social_score - news_score
    
    if abs(delta) < 0.1:
        return "Social media and official news are aligned"
    elif delta > 0.3:
        return "⚠️ Social media is MUCH MORE BULLISH than news - retail investors optimistic despite negative news"
    elif delta > 0.1:
        return "Social media is more bullish than official news"
    elif delta < -0.3:
        return "⚠️ Social media is MUCH MORE BEARISH than news - retail investors pessimistic despite positive news"
    elif delta < -0.1:
        return "Social media is more bearish than official news"
    else:
        return "Sentiment aligned"


@router.post("/search-social-media-batch", summary="🐦 Batch search multiple tickers")
async def search_social_media_batch_endpoint(
    tickers: List[str],
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """
    Search social media for multiple tickers in batch.
    
    **Example:** `POST /search-social-media-batch` with body `["SFBT", "BIAT", "BNA"]`
    
    Returns aggregated sentiment for each ticker.
    """
    if len(tickers) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 tickers allowed per batch request"
        )
    
    results = await search_social_media_batch([t.upper() for t in tickers])
    
    # Analyze posts for each ticker
    ticker_sentiments = {}
    for ticker, posts in results.items():
        if not posts:
            ticker_sentiments[ticker] = {
                "posts_found": 0,
                "sentiment": None,
            }
            continue
        
        analyzed_posts = []
        for post in posts[:20]:  # Limit to 20 per ticker
            try:
                title = post.content[:100] if post.content else ""
                snippet = post.content[100:] if len(post.content) > 100 else ""
                
                sentiment_result = await analyze_sentiment(
                    title=title,
                    snippet=snippet if snippet else None,
                    language="tn",
                    enable_tunizi=True,
                )
                analyzed_posts.append({
                    "sentiment": sentiment_result.sentiment,
                    "score": sentiment_result.score,
                })
            except Exception:
                continue
        
        scores = [p["score"] for p in analyzed_posts]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        overall = "positive" if avg_score > 0.15 else ("negative" if avg_score < -0.15 else "neutral")
        
        ticker_sentiments[ticker] = {
            "posts_found": len(posts),
            "posts_analyzed": len(analyzed_posts),
            "sentiment": overall,
            "avg_score": round(avg_score, 3),
        }
    
    return {
        "tickers_searched": len(tickers),
        "results": ticker_sentiments,
    }
