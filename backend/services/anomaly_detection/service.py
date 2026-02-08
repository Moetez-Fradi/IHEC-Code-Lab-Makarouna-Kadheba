"""
Anomaly Detection – Core detection logic
─────────────────────────────────────────
Three detectors run on the daily data for a given company:

1. **Volume z-score** – rolling z-score on QUANTITE_NEGOCIEE (>3 σ)
2. **Price gap**       – day-over-day OUVERTURE/CLOTURE change (>5 %)
3. **Pattern (IF)**    – Isolation Forest on NB_TRANSACTION × CAPITAUX

Results are merged into a unified severity score per day.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from algo_config import config
from db import fetch_company_data

logger = logging.getLogger(__name__)


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class DayAnomaly:
    """One anomaly record for a single trading day."""
    date: str
    types: list[str] = field(default_factory=list)  # e.g. ["volume", "price"]
    severity: float = 0.0                           # 0 – 1
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyReport:
    """Complete report returned by the service."""
    code: str
    start: str
    end: str
    total_days: int
    anomaly_days: int
    anomalies: list[dict[str, Any]]
    summary: dict[str, Any]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _safe_float(v: Any) -> float:
    """Convert DB value to float, treating None / NaN as 0."""
    if v is None:
        return 0.0
    f = float(v)
    return 0.0 if np.isnan(f) else f


# ── Detectors ─────────────────────────────────────────────────────────────────


def detect_volume_anomalies(df: pd.DataFrame) -> pd.Series:
    """
    Rolling z-score on QUANTITE_NEGOCIEE.
    Returns a boolean Series (True = anomaly).
    """
    vol = df["QUANTITE_NEGOCIEE"].astype(float)
    window = config.volume_rolling_window

    rolling_mean = vol.rolling(window=window, min_periods=1).mean()
    rolling_std = vol.rolling(window=window, min_periods=1).std().fillna(0)

    zscore = pd.Series(0.0, index=df.index)
    mask = rolling_std > 0
    zscore[mask] = (vol[mask] - rolling_mean[mask]) / rolling_std[mask]

    df["_vol_zscore"] = zscore
    return zscore.abs() > config.volume_zscore_threshold


def detect_price_anomalies(df: pd.DataFrame) -> pd.Series:
    """
    Day-over-day percentage change of CLOTURE (or OUVERTURE if CLOTURE is
    missing).  Flagged when |change| > threshold (default 5 %).
    Returns a boolean Series.
    """
    close = df["CLOTURE"].astype(float).replace(0, np.nan)
    openp = df["OUVERTURE"].astype(float).replace(0, np.nan)
    price = close.fillna(openp).ffill()

    pct = price.pct_change().fillna(0)
    df["_price_pct"] = pct
    return pct.abs() > config.price_change_threshold


def detect_pattern_anomalies(df: pd.DataFrame) -> pd.Series:
    """
    Isolation Forest on (NB_TRANSACTION, CAPITAUX).
    Returns a boolean Series (True = anomaly / outlier).
    """
    features = df[["NB_TRANSACTION", "CAPITAUX"]].astype(float).fillna(0)

    if len(features) < 10:
        # Not enough data for meaningful isolation forest
        df["_if_score"] = 0.0
        return pd.Series(False, index=df.index)

    iso = IsolationForest(
        n_estimators=config.isolation_n_estimators,
        contamination=config.isolation_contamination,
        random_state=config.isolation_random_state,
    )
    preds = iso.fit_predict(features.values)
    scores = iso.decision_function(features.values)

    df["_if_score"] = scores
    return pd.Series(preds == -1, index=df.index)


# ── Merge & score ─────────────────────────────────────────────────────────────


def _compute_severity(
    vol_flag: bool,
    price_flag: bool,
    pattern_flag: bool,
    vol_zscore: float,
    price_pct: float,
    if_score: float,
) -> float:
    """
    Weighted severity in [0, 1].
    Each component is normalised then weighted.
    """
    # Normalise individual signals to 0-1
    vol_sev = min(abs(vol_zscore) / 6.0, 1.0) if vol_flag else 0.0
    price_sev = min(abs(price_pct) / 0.15, 1.0) if price_flag else 0.0
    # IF decision_function: more negative → more anomalous
    pattern_sev = min(max(-if_score, 0) / 0.3, 1.0) if pattern_flag else 0.0

    raw = (
        config.weight_volume * vol_sev
        + config.weight_price * price_sev
        + config.weight_pattern * pattern_sev
    )
    return round(min(raw, 1.0), 4)


def merge_anomalies(df: pd.DataFrame) -> list[DayAnomaly]:
    """Run all three detectors and merge into per-day anomaly records."""

    vol_flags = detect_volume_anomalies(df)
    price_flags = detect_price_anomalies(df)
    pattern_flags = detect_pattern_anomalies(df)

    anomalies: list[DayAnomaly] = []

    for idx in df.index:
        vf = bool(vol_flags[idx])
        pf = bool(price_flags[idx])
        patf = bool(pattern_flags[idx])

        if not (vf or pf or patf):
            continue

        types: list[str] = []
        if vf:
            types.append("volume")
        if pf:
            types.append("price")
        if patf:
            types.append("pattern")

        severity = _compute_severity(
            vf, pf, patf,
            float(df.at[idx, "_vol_zscore"]),
            float(df.at[idx, "_price_pct"]),
            float(df.at[idx, "_if_score"]),
        )

        details: dict[str, Any] = {
            "SEANCE": str(df.at[idx, "SEANCE"]),
            "OUVERTURE": _safe_float(df.at[idx, "OUVERTURE"]),
            "CLOTURE": _safe_float(df.at[idx, "CLOTURE"]),
            "QUANTITE_NEGOCIEE": _safe_float(df.at[idx, "QUANTITE_NEGOCIEE"]),
            "NB_TRANSACTION": _safe_float(df.at[idx, "NB_TRANSACTION"]),
            "CAPITAUX": _safe_float(df.at[idx, "CAPITAUX"]),
            "volume_zscore": round(float(df.at[idx, "_vol_zscore"]), 4),
            "price_change_pct": round(float(df.at[idx, "_price_pct"]) * 100, 2),
            "isolation_score": round(float(df.at[idx, "_if_score"]), 4),
        }

        anomalies.append(DayAnomaly(
            date=str(df.at[idx, "SEANCE"]),
            types=types,
            severity=severity,
            details=details,
        ))

    return anomalies


# ── Public API ────────────────────────────────────────────────────────────────


async def run_anomaly_detection(
    code: str,
    start: str,
    end: str,
) -> AnomalyReport:
    """
    End-to-end pipeline:
    1. Fetch data from Postgres
    2. Build DataFrame
    3. Run detectors
    4. Merge into severity-scored report
    """
    rows = await fetch_company_data(code, start, end)

    if not rows:
        return AnomalyReport(
            code=code,
            start=start,
            end=end,
            total_days=0,
            anomaly_days=0,
            anomalies=[],
            summary={"message": "No data found for the given parameters."},
        )

    df = pd.DataFrame(rows)

    # Ensure numeric types
    numeric_cols = [
        "OUVERTURE", "CLOTURE", "PLUS_HAUT", "PLUS_BAS",
        "QUANTITE_NEGOCIEE", "CAPITAUX", "NB_TRANSACTION",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    day_anomalies = merge_anomalies(df)

    # ── Summary stats ────────────────────────────────────────
    severity_values = [a.severity for a in day_anomalies]
    type_counts: dict[str, int] = {}
    for a in day_anomalies:
        for t in a.types:
            type_counts[t] = type_counts.get(t, 0) + 1

    summary = {
        "avg_severity": round(np.mean(severity_values), 4) if severity_values else 0,
        "max_severity": round(max(severity_values), 4) if severity_values else 0,
        "type_counts": type_counts,
        "volume_anomalies": type_counts.get("volume", 0),
        "price_anomalies": type_counts.get("price", 0),
        "pattern_anomalies": type_counts.get("pattern", 0),
    }

    return AnomalyReport(
        code=code,
        start=start,
        end=end,
        total_days=len(df),
        anomaly_days=len(day_anomalies),
        anomalies=[
            {
                "date": a.date,
                "types": a.types,
                "severity": a.severity,
                "details": a.details,
            }
            for a in day_anomalies
        ],
        summary=summary,
    )
