"""
LLM service — analyses article text via Google Gemini Flash Lite.

Returns structured sentiment: label, score, and optional ticker match.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import List

import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content

from app.config import LLM_MODEL, GEMINI_API_KEY, TICKERS

logger = logging.getLogger(__name__)

# ── Gemini Client Configuration ─────────────────────────

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY is not set. LLM features will fail.")

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
    "  If no specific company is mentioned, return null."
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

    # If simple parsing fails, return safe default
    logger.warning("Failed to parse JSON from Gemini response: %s", text[:100])
    return {"sentiment": "neutral", "score": 0.0, "ticker": None}


# ── Public API ──────────────────────────────────────────

async def analyze_sentiment(
    title: str,
    snippet: str | None = None,
    language: str = "fr",
) -> SentimentResult:
    """
    Send a single article to Gemini and return structured sentiment.
    """
    if not GEMINI_API_KEY:
        return SentimentResult(error="Missing configuration: GEMINI_API_KEY")

    user_content = f"Language: {language}\nTitle: {title}"
    if snippet and snippet != title:
        user_content += f"\nSnippet: {snippet[:800]}"  # Truncate to save context

    try:
        model = genai.GenerativeModel(
            model_name=LLM_MODEL,
            system_instruction=_SYSTEM_PROMPT,
            generation_config={"response_mime_type": "application/json"}
        )

        response = await model.generate_content_async(user_content)
        
        raw = response.text
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
        logger.exception("Gemini analysis failed for: %s", title[:80])
        return SentimentResult(error=str(exc))


async def analyze_batch(
    articles: List[dict],
) -> List[SentimentResult]:
    """
    Analyse a list of article dicts (each with 'title', 'content_snippet', 'language').
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
