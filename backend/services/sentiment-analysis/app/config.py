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

# ── OpenRouter ──────────────────────────────────────────
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
LLM_MODEL: str = "tngtech/deepseek-r1t2-chimera:free"

# ── Database ────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./sentiment.db",
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
