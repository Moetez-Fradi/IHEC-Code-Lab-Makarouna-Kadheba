"""
Anomaly Detection – Configuration
Thresholds, rolling windows, and DB settings are all tuneable here.
"""

import os
from dataclasses import dataclass, field


@dataclass
class AnomalyConfig:
    # ── Database ──────────────────────────────────────────────
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://neondb_owner:npg_bog2kaSA1DNZ@ep-shy-breeze-ag2f4327-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require",
        )
    )

    # ── Volume z-score ────────────────────────────────────────
    volume_rolling_window: int = 20          # days
    volume_zscore_threshold: float = 3.0     # σ

    # ── Price change ──────────────────────────────────────────
    price_change_threshold: float = 0.05     # 5 %

    # ── Isolation Forest (NB_TRANSACTION + CAPITAUX) ──────────
    isolation_contamination: float = 0.05    # expected anomaly fraction
    isolation_n_estimators: int = 100
    isolation_random_state: int = 42

    # ── Severity weights ──────────────────────────────────────
    weight_volume: float = 0.35
    weight_price: float = 0.35
    weight_pattern: float = 0.30

    # ── Service ───────────────────────────────────────────────
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8001")))


config = AnomalyConfig()
