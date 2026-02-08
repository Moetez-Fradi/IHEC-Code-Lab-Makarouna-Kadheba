"""
Aggregation logic — computes daily sentiment scores per ticker
from the articles stored in the database.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Article, DailySentiment

logger = logging.getLogger(__name__)


async def compute_daily_scores(session: AsyncSession) -> List[DailySentiment]:
    """
    For each ticker that has articles today, calculate the average
    sentiment score and upsert a ``DailySentiment`` row.

    Returns the list of created / updated ``DailySentiment`` objects.
    """
    today_start = dt.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + dt.timedelta(days=1)

    # Aggregate: AVG(score), COUNT(*) grouped by ticker for today
    stmt = (
        select(
            Article.ticker,
            func.avg(Article.score).label("avg_score"),
            func.count(Article.id).label("cnt"),
        )
        .where(
            Article.ticker.isnot(None),
            Article.score.isnot(None),
            Article.created_at >= today_start,
            Article.created_at < tomorrow_start,
        )
        .group_by(Article.ticker)
    )

    rows = (await session.execute(stmt)).all()

    results: list[DailySentiment] = []

    for ticker, avg_score, cnt in rows:
        # Check if a row already exists for this ticker + date
        existing_stmt = select(DailySentiment).where(
            DailySentiment.ticker == ticker,
            DailySentiment.date >= today_start,
            DailySentiment.date < tomorrow_start,
        )
        existing = (await session.execute(existing_stmt)).scalar_one_or_none()

        if existing:
            existing.avg_score = round(float(avg_score), 4)
            existing.article_count = int(cnt)
            results.append(existing)
        else:
            ds = DailySentiment(
                ticker=ticker,
                date=today_start,
                avg_score=round(float(avg_score), 4),
                article_count=int(cnt),
            )
            session.add(ds)
            results.append(ds)

    await session.commit()
    logger.info("Aggregated daily scores for %d tickers", len(results))
    return results


async def get_today_scores(session: AsyncSession) -> List[DailySentiment]:
    """Return all ``DailySentiment`` rows for today."""
    today_start = dt.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + dt.timedelta(days=1)

    stmt = select(DailySentiment).where(
        DailySentiment.date >= today_start,
        DailySentiment.date < tomorrow_start,
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
