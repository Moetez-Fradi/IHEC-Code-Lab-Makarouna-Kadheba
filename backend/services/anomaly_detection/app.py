"""
Anomaly Detection – FastAPI application
────────────────────────────────────────
Runs on port 8001 (configurable via env PORT).
Called by the NestJS core backend or directly by the frontend.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from algo_config import config
from db import init_pool, close_pool
from service import run_anomaly_detection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting anomaly-detection service …")
    await init_pool()
    yield
    await close_pool()
    logger.info("Anomaly-detection service shut down.")


# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BVMT Anomaly Detection",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "anomaly-detection"}


@app.get("/anomalies")
async def get_anomalies(
    code: str = Query(..., description="Company stock code, e.g. 'PX1'"),
    start: str = Query(..., description="Start date inclusive (YYYY-MM-DD)"),
    end: str = Query(..., description="End date inclusive (YYYY-MM-DD)"),
):
    """
    Run the full anomaly-detection pipeline for a company within a date range.

    Returns a JSON report with:
    - per-day anomalies (date, type, severity, detailed metrics)
    - summary statistics
    """
    if not code:
        raise HTTPException(status_code=400, detail="'code' query param is required")
    if not start or not end:
        raise HTTPException(status_code=400, detail="'start' and 'end' query params are required")

    try:
        report = await run_anomaly_detection(code, start, end)
        return asdict(report)
    except Exception as exc:
        logger.exception("Anomaly detection failed for code=%s", code)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/config")
async def get_config():
    """Expose the current (non-secret) configuration for debugging."""
    return {
        "volume_rolling_window": config.volume_rolling_window,
        "volume_zscore_threshold": config.volume_zscore_threshold,
        "price_change_threshold": config.price_change_threshold,
        "isolation_contamination": config.isolation_contamination,
        "isolation_n_estimators": config.isolation_n_estimators,
        "weight_volume": config.weight_volume,
        "weight_price": config.weight_price,
        "weight_pattern": config.weight_pattern,
    }


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=config.host,
        port=config.port,
        reload=True,
    )
