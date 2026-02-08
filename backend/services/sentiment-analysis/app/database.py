"""
SQLAlchemy async engine, session factory, and ORM models for SQLite.
"""

from __future__ import annotations

import datetime as dt
from typing import AsyncGenerator

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import DATABASE_URL

# ── Engine & session ────────────────────────────────────
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared base for all ORM models."""


# ── Models ──────────────────────────────────────────────


class Article(Base):
    """A single news article with its computed sentiment."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(64), nullable=False, index=True)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=True)
    content_snippet = Column(Text, nullable=True)
    language = Column(String(8), nullable=False, default="fr")

    # Sentiment fields (filled after LLM analysis)
    sentiment = Column(String(16), nullable=True)   # positive / negative / neutral
    score = Column(Float, nullable=True)             # -1.0 … 1.0
    ticker = Column(String(32), nullable=True)       # matched ticker or NULL

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        default=dt.datetime.utcnow,
    )


class DailySentiment(Base):
    """Pre-aggregated daily sentiment score per ticker."""

    __tablename__ = "daily_sentiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(32), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    avg_score = Column(Float, nullable=False)
    article_count = Column(Integer, nullable=False, default=0)


# ── Helpers ─────────────────────────────────────────────


async def init_db() -> None:
    """Create all tables if they don't exist yet."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with async_session_factory() as session:
        yield session
