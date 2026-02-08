"""
Forecasting Service – Configuration
Database settings and model parameters.
"""

import os
from dataclasses import dataclass, field


@dataclass
class ForecastConfig:
    # ── Database ──────────────────────────────────────────────
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://neondb_owner:npg_bog2kaSA1DNZ@ep-shy-breeze-ag2f4327-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require",
        )
    )

    # ── Model parameters ─────────────────────────────────────
    forecast_horizon: int = 5              # days ahead
    min_history_days: int = 120            # minimum data needed to train
    default_lookback_days: int = 500       # fetch this many days for training

    # ── XGBoost hyper-params ─────────────────────────────────
    xgb_n_estimators: int = 500
    xgb_max_depth: int = 6
    xgb_learning_rate: float = 0.05
    xgb_subsample: float = 0.8
    xgb_colsample_bytree: float = 0.8
    xgb_early_stopping: int = 30

    # ── Volume model ─────────────────────────────────────────
    vol_n_estimators: int = 300
    vol_max_depth: int = 5

    # ── Liquidity classifier ─────────────────────────────────
    liq_n_estimators: int = 200
    liq_max_depth: int = 8

    # ── Service ───────────────────────────────────────────────
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8002")))


config = ForecastConfig()
