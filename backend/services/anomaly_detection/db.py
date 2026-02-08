from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg
from config import config

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    """Create / return the connection pool (lazy singleton)."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=config.database_url,
            min_size=2,
            max_size=10,
            ssl="require",
        )
        logger.info("Database pool created")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


@asynccontextmanager
async def get_connection() -> AsyncIterator[asyncpg.Connection]:
    pool = await init_pool()
    async with pool.acquire() as conn:
        yield conn


async def fetch_company_data(
    code: str,
    start: str,
    end: str,
) -> list[dict]:
    """
    Return all rows for *code* between *start* and *end* (inclusive),
    ordered by SEANCE ascending.
    """
    query = """
        SELECT
            "CODE",
            "VALEUR",
            "SEANCE",
            "OUVERTURE",
            "CLOTURE",
            "PLUS_HAUT",
            "PLUS_BAS",
            "QUANTITE_NEGOCIEE",
            "CAPITAUX",
            "NB_TRANSACTION",
            "GROUPE"
        FROM bvmt_data
        WHERE "CODE" = $1
          AND "SEANCE" >= $2
          AND "SEANCE" <= $3
        ORDER BY "SEANCE" ASC
    """
    async with get_connection() as conn:
        rows = await conn.fetch(query, code, start, end)

    return [dict(r) for r in rows]
