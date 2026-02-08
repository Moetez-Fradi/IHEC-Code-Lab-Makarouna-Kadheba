"""
LLM service — analyses article text via OpenRouter (Gemini Flash Lite).

Returns structured sentiment: label, score, and optional ticker match.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import List

from openai import AsyncOpenAI

from app.config import LLM_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL, TICKERS

logger = logging.getLogger(__name__)

# ── OpenRouter client (OpenAI-compatible) ───────────────

_client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

# ── Prompt template ─────────────────────────────────────

_TICKERS_STR = ", ".join(TICKERS)

_SYSTEM_PROMPT = (
    "You are a financial sentiment analysis expert specializing in the "
    "Tunis Stock Exchange (BVMT).\n"
    "You understand French, Arabic, and Tunisian dialect perfectly.\n\n"
    "Given a news article title and snippet, return a JSON object with "
    "EXACTLY these keys:\n\n"
    '{\n'
    '  "sentiment": "positive" | "negative" | "neutral",\n'
    '  "score": <float between -1.0 and 1.0>,\n'
    '  "ticker": "<TICKER>" or null\n'
    '}\n\n'
    "Rules:\n"
    '- sentiment: "positive" if the news is good for the company/market, '
    '"negative" if bad, "neutral" otherwise.\n'
    "- score: a float from -1.0 (very negative) to 1.0 (very positive). "
    "0.0 = neutral.\n"
    "- ticker: if the article clearly mentions one of these Tunisian "
    f"companies, return the ticker symbol.\n  Known tickers: {_TICKERS_STR}.\n"
    '  Match company names to tickers (e.g., '
    '"Société Frigorifique et Brasserie de Tunis" -> "SFBT", '
    '"Banque Internationale Arabe de Tunisie" -> "BIAT", '
    '"Poulina Group Holding" -> "POULINA", '
    '"Société d\'Articles Hygiéniques" -> "SAH", '
    '"Délice Holding" -> "DELICE", '
    '"Banque Nationale Agricole" -> "BNA", '
    '"Ciments de Carthage" -> "CARTHAGE", '
    '"Euro-Cycles" -> "EURO-CYCLES", '
    '"Telnet Holding" -> "TELNET", '
    '"Tunisair" -> "TUNISAIR").\n'
    "  If no specific company is mentioned, return null.\n\n"
    "Return ONLY the raw JSON object, nothing else. No markdown, no explanation."
)


# ── Result container ────────────────────────────────────

@dataclass
class SentimentResult:
    sentiment: str = "neutral"
    score: float = 0.0
    ticker: str | None = None
    error: str | None = None


# ── JSON extraction helper ──────────────────────────────

_JSON_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _parse_llm_json(text: str) -> dict:
    """Best-effort extraction of JSON from LLM response."""
    # Try raw parse first
    text = text.strip()
    if text.startswith("```"):
        # strip markdown fences
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: find first JSON-like object
    m = _JSON_RE.search(text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from LLM response: {text[:200]}")


# ── Public API ──────────────────────────────────────────

async def analyze_sentiment(
    title: str,
    snippet: str | None = None,
    language: str = "fr",
) -> SentimentResult:
    """
    Send a single article to the LLM and return structured sentiment.
    """
    user_content = f"Language: {language}\nTitle: {title}"
    if snippet and snippet != title:
        user_content += f"\nSnippet: {snippet[:500]}"

    try:
        response = await _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.0,
            max_tokens=200,
        )

        raw = response.choices[0].message.content or ""
        data = _parse_llm_json(raw)

        sentiment = str(data.get("sentiment", "neutral")).lower()
        if sentiment not in ("positive", "negative", "neutral"):
            sentiment = "neutral"

        score = float(data.get("score", 0.0))
        score = max(-1.0, min(1.0, score))

        ticker = data.get("ticker")
        if ticker and str(ticker).upper() not in TICKERS:
            ticker = None
        elif ticker:
            ticker = str(ticker).upper()

        return SentimentResult(sentiment=sentiment, score=score, ticker=ticker)

    except Exception as exc:
        logger.exception("LLM analysis failed for: %s", title[:80])
        return SentimentResult(error=str(exc))


async def analyze_batch(
    articles: List[dict],
) -> List[SentimentResult]:
    """
    Analyse a list of article dicts (each with 'title', 'content_snippet', 'language').
    Processes sequentially to respect free-tier rate limits.
    """
    results: list[SentimentResult] = []
    for art in articles:
        res = await analyze_sentiment(
            title=art["title"],
            snippet=art.get("content_snippet"),
            language=art.get("language", "fr"),
        )
        results.append(res)
    return results
