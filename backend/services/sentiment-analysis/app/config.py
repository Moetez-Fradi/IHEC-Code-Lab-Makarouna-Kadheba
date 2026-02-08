"""
Application-wide configuration loaded from environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env from project root ────────────────────────
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    load_dotenv()  # fallback: look in cwd

# ── Gemini (Google AI) ──────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL: str = "gemini-flash-lite-latest"

# ── Perplexity AI (Social Media Search) ─────────────────
PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_MODEL: str = "sonar"  # Real-time search model

# ── Database ────────────────────────────────────────────
# Note: sslmode is removed because asyncpg handles SSL automatically
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_bog2kaSA1DNZ@ep-shy-breeze-ag2f4327-pooler.c-2.eu-central-1.aws.neon.tech/neondb",
)

# ── Tunisian tickers we care about ──────────────────────
TICKERS: list[str] = [
    "SFBT",
    "BIAT",
    "BNA",
    "SAH",
    "CARTHAGE",
    "POULINA",
    "DELICE",
    "EURO-CYCLES",
    "TELNET",
    "TUNISAIR",
]

# ── Scraper targets ────────────────────────────────────
SCRAPER_SOURCES: list[dict] = [
    {
        "name": "IlBoursa",
        "url": "https://www.ilboursa.com/marches/actualites_bourse_tunis",
        "lang": "fr",
    },
    {
        "name": "Tustex",
        "url": "https://www.tustex.com/bourse-tunis",
        "lang": "fr",
    },
    {
        "name": "TunisieNumerique",
        "url": "https://www.tunisienumerique.com/actualite-tunisie/economie/",
        "lang": "ar",
    },
]

# ── App meta ────────────────────────────────────────────
APP_NAME: str = os.getenv("APP_NAME", "BVMT Sentiment Analysis")
DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
