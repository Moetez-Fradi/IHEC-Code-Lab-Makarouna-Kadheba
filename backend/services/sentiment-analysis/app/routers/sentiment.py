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

