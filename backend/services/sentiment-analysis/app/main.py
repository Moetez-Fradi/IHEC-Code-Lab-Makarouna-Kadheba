"""
BVMT Sentiment Analysis — FastAPI entry point.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_NAME, DEBUG
from app.database import init_db
from app.routers.sentiment import router as sentiment_router

# ── Logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ───────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("🔧 Initialising database …")
    await init_db()
    logger.info("✅ Database ready")
    yield
    logger.info("👋 Shutting down")


# ── App factory ─────────────────────────────────────────
app = FastAPI(
    title=APP_NAME,
    version="1.0.0",
    description=(
        "Lightweight sentiment analysis module for the Tunis Stock Exchange (BVMT). "
        "Scrapes Tunisian financial news, analyses sentiment via OpenRouter LLM, "
        "and exposes aggregated daily scores per ticker."
    ),
    lifespan=lifespan,
)

# ── CORS (allow any origin for hackathon) ───────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────
app.include_router(sentiment_router)


# ── Health check ────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME}
