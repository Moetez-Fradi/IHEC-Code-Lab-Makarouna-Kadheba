"""
Forecasting Service – FastAPI application
──────────────────────────────────────────
Runs on port 8002 (configurable via env PORT).
Called by the NestJS core backend or directly by the frontend.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config import config
from db import init_pool, close_pool
from service import run_forecast

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting forecasting service on port %s …", config.port)
    await init_pool()
    yield
    await close_pool()
    logger.info("Forecasting service shut down.")


# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BVMT Forecasting Service",
    version="1.0.0",
    description="Predict closing price, volume, and liquidity for the next 5 business days.",
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
    return {"status": "ok", "service": "forecasting"}


@app.get("/forecast")
async def get_forecast(
    code: str = Query(..., description="Stock code, e.g. 'TN0001100254'"),
    lookback: int = Query(None, description="Number of historical days to use for training (default 500)"),
):
    """
    Run the full forecasting pipeline for a stock.

    Returns:
    - 5-day price forecast with confidence intervals
    - Volume forecasts per day
    - Liquidity probability per day
    - Model validation metrics (RMSE, MAE, MAPE, Directional Accuracy)
    - Historical close prices for chart context
    """
    if not code:
        raise HTTPException(status_code=400, detail="'code' query param is required")

    try:
        report = await run_forecast(code, lookback)
        return asdict(report)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Forecasting failed for code=%s", code)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/config")
async def get_config():
    """Expose the current (non-secret) configuration for debugging."""
    return {
        "forecast_horizon": config.forecast_horizon,
        "min_history_days": config.min_history_days,
        "default_lookback_days": config.default_lookback_days,
        "xgb_n_estimators": config.xgb_n_estimators,
        "xgb_max_depth": config.xgb_max_depth,
        "port": config.port,
    }


# ── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.host, port=config.port, reload=True)
