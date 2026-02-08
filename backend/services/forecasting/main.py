"""
Forecasting Service – FastAPI application
──────────────────────────────────────────
Runs on port 8002 (configurable via env PORT).
Called by the NestJS core backend or directly by the frontend.

Enhanced with Tunisian macro-economic features (K.O. Feature #2).
"""

from __future__ import annotations

import datetime as dt
import logging
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config import config
from db import init_pool, close_pool
from service import run_forecast
from macro_features import get_macro_snapshot, get_macro_features_for_stock, get_macro_explanation

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


# ── 🇹🇳 K.O. FEATURE #2: Macro-Economic Data ────────────────────────────────

@app.get("/macro")
async def get_macro_data(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)"),
):
    """
    **K.O. FEATURE #2** - Tunisian Macro-Economic Indicators
    
    Returns macro data that enhances stock predictions:
    - 📦 Phosphate Production (CPG) + Global DAP prices
    - 💰 TMM (Taux Moyen du Marché - BCT)
    - ✈️ Tourism Arrivals (ONTT)
    
    This is THE differentiator: we integrate Tunisia-specific economic factors
    that affect different sectors:
    - Phosphates → Industrial/Materials/Transport
    - TMM → Banking (positive) / Leasing & Real Estate (negative)
    - Tourism → Consumption/Hospitality/Services
    
    **Why this matters:**
    "We don't just copy NYSE models. We understand Tunisia's economy."
    """
    try:
        target_date = dt.date.fromisoformat(date) if date else dt.date.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    snapshot = get_macro_snapshot(target_date)
    
    result = {
        "date": str(snapshot.date),
        "phosphate": None,
        "tmm": None,
        "tourism": None,
    }
    
    if snapshot.phosphate:
        result["phosphate"] = {
            "production_kt": snapshot.phosphate.production_kt,
            "global_price_usd": snapshot.phosphate.global_price_usd,
            "notes": snapshot.phosphate.notes,
            "impact": "Affects Industrial, Materials, Transport sectors",
        }
    
    if snapshot.tmm:
        result["tmm"] = {
            "rate_percent": snapshot.tmm.rate,
            "change_bps": snapshot.tmm.change_bps,
            "direction": "↑" if snapshot.tmm.change_bps > 0 else "↓" if snapshot.tmm.change_bps < 0 else "→",
            "impact_positive": "Banking sector benefits from high rates",
            "impact_negative": "Leasing and Real Estate hurt by high rates",
        }
    
    if snapshot.tourism:
        result["tourism"] = {
            "arrivals_thousands": snapshot.tourism.arrivals,
            "yoy_change_percent": snapshot.tourism.yoy_change,
            "impact": "Affects Consumption, Hospitality, Services sectors",
        }
    
    return result


@app.get("/macro/features")
async def get_macro_features(
    sector: str = Query(..., description="Stock sector (e.g., 'Banques', 'Consommation')"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)"),
):
    """
    Get normalized macro feature vector for ML model.
    
    Returns features scaled to [-1, 1] for direct input to XGBoost/TFT models.
    Includes sector-specific weights (e.g., TMM has 1.0 weight for banks, -1.0 for leasing).
    """
    try:
        target_date = dt.date.fromisoformat(date) if date else dt.date.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    features = get_macro_features_for_stock(sector, target_date)
    explanation = get_macro_explanation(sector, target_date)
    
    return {
        "sector": sector,
        "date": str(target_date),
        "features": features,
        "explanation": explanation,
    }


# ── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.host, port=config.port, reload=True)
