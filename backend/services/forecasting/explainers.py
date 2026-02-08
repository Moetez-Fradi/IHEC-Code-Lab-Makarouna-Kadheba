"""
Forecast explainability module.

Provides:
  • SHAP-value computation (feature importance per prediction).
  • Confidence-interval estimation from the quantile spread.
  • Top-driver identification with human-readable labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


# Feature display names for readability
_FEATURE_LABELS: Dict[str, str] = {
    "close": "Closing price",
    "open": "Opening price",
    "high": "Daily high",
    "low": "Daily low",
    "volume": "Trading volume",
    "spread": "Bid-ask spread",
    "depth": "Order-book depth",
    "imbalance": "Order imbalance",
    "rsi": "RSI (14)",
    "macd": "MACD",
    "news_sentiment": "News sentiment score",
}


class ForecastExplainer:
    """
    Compute SHAP-like attributions and confidence intervals for a
    forecasting prediction.

    In production, plug in ``shap.TreeExplainer`` or
    ``shap.DeepExplainer`` around the real model.  The numpy
    reference implementation uses a simple perturbation-based
    approximation (feature-ablation SHAP).
    """

    def __init__(self, baseline: Optional[Dict[str, float]] = None):
        """
        Parameters
        ----------
        baseline : feature-value dict representing the "average" input.
                   Used as the reference for SHAP attribution.
        """
        self.baseline = baseline or {}

    # ------------------------------------------------------------------
    def compute_shap(
        self,
        features: Dict[str, float],
        predict_fn=None,
    ) -> Dict[str, float]:
        """
        Feature-ablation SHAP approximation.

        For each feature *f*, the attribution is defined as::

            shap[f] = predict(full) − predict(full with f replaced by baseline)

        Parameters
        ----------
        features   : current input feature dict.
        predict_fn : callable(dict) -> float  (returns scalar forecast).

        Returns
        -------
        Dict mapping feature name → SHAP value.
        """
        if predict_fn is None:
            # Fallback: use variance-scaled heuristic
            return self._heuristic_shap(features)

        full_pred = predict_fn(features)
        shap_values: Dict[str, float] = {}

        for key in features:
            ablated = dict(features)
            ablated[key] = self.baseline.get(key, 0.0)
            ablated_pred = predict_fn(ablated)
            shap_values[key] = round(full_pred - ablated_pred, 6)

        return shap_values

    # ------------------------------------------------------------------
    def confidence_interval(
        self,
        p10: float,
        p90: float,
        confidence: float = 0.80,
    ) -> Tuple[float, float]:
        """
        Derive a symmetric confidence interval from quantile forecasts.

        The 80 % CI is simply [p10, p90].  For other levels we
        interpolate / extrapolate assuming a Gaussian tail.
        """
        mid = (p10 + p90) / 2
        half_width = (p90 - p10) / 2  # ≈ 1.28 σ for 80 %

        if abs(confidence - 0.80) < 1e-6:
            return (round(p10, 4), round(p90, 4))

        # Scale half-width by ratio of z-scores
        z_80 = 1.2816
        z_map: Dict[float, float] = {
            0.90: 1.6449,
            0.95: 1.9600,
            0.99: 2.5758,
            0.50: 0.6745,
        }
        z_target = z_map.get(round(confidence, 2), 1.2816)
        scaled = half_width * (z_target / z_80)

        return (round(mid - scaled, 4), round(mid + scaled, 4))

    # ------------------------------------------------------------------
    def top_drivers(
        self,
        shap_values: Dict[str, float],
        top_k: int = 5,
    ) -> List[Dict[str, object]]:
        """
        Return the *top_k* features ranked by |SHAP|.
        """
        ranked = sorted(shap_values.items(), key=lambda kv: abs(kv[1]), reverse=True)
        return [
            {
                "feature": k,
                "label": _FEATURE_LABELS.get(k, k),
                "shap_value": v,
                "direction": "positive" if v > 0 else "negative",
            }
            for k, v in ranked[:top_k]
        ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _heuristic_shap(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Variance-based heuristic when no predict_fn is supplied.

        Assigns importance proportional to |feature − baseline| scaled
        by a hand-tuned weight per feature category.
        """
        weights: Dict[str, float] = {
            "volume": 0.30,
            "close": 0.20,
            "spread": 0.15,
            "depth": 0.10,
            "rsi": 0.10,
            "open": 0.05,
            "high": 0.03,
            "low": 0.03,
            "imbalance": 0.02,
            "news_sentiment": 0.02,
        }
        shap_vals: Dict[str, float] = {}
        for key, val in features.items():
            base = self.baseline.get(key, 0.0)
            w = weights.get(key, 0.01)
            shap_vals[key] = round(w * (val - base), 6)

        return shap_vals
