"""Risk-profile-aware weight adjustment.

Each profile caps concentration and volatility exposure:
  - conservateur → max 15 % per asset, clip vol to 20 % annualised
  - modéré       → max 25 % per asset
  - agressif     → raw RL weights, allow high concentration
"""

import numpy as np

from app.core.types import RiskProfile

# ── per-profile parameters ────────────────────────────────
_PARAMS: dict[RiskProfile, dict] = {
    RiskProfile.CONSERVATEUR: {
        "max_weight": 0.15,
        "vol_cap": 0.20,     # penalise assets with ann. vol > 20 %
        "cash_floor": 0.10,  # keep ≥ 10 % cash
    },
    RiskProfile.MODERE: {
        "max_weight": 0.25,
        "vol_cap": 0.35,
        "cash_floor": 0.05,
    },
    RiskProfile.AGRESSIF: {
        "max_weight": 0.50,
        "vol_cap": 1.0,
        "cash_floor": 0.0,
    },
}


def adjust_weights(
    raw_weights: np.ndarray,
    profile: RiskProfile,
    volatilities: np.ndarray | None = None,
) -> np.ndarray:
    """Adjust RL-recommended weights to the user's risk profile."""
    p = _PARAMS[profile]
    w = raw_weights.copy().astype(float)

    # 1. Cap individual positions
    w = np.minimum(w, p["max_weight"])

    # 2. Penalise high-vol assets for conservative profiles
    if volatilities is not None and p["vol_cap"] < 1.0:
        penalty = np.clip(volatilities / p["vol_cap"], 0.0, 2.0)
        w = w / np.maximum(penalty, 1.0)

    # 3. Enforce cash floor by scaling down
    invested = w.sum()
    max_invest = 1.0 - p["cash_floor"]
    if invested > max_invest and invested > 0:
        w = w * (max_invest / invested)

    # 4. Re-normalise so invested portion sums to ≤ 1
    total = w.sum()
    if total > 1.0:
        w = w / total

    return w


def profile_description(profile: RiskProfile) -> str:
    """Human-readable summary of a profile for the LLM prompt."""
    descs = {
        RiskProfile.CONSERVATEUR: (
            "Profil conservateur : priorité à la préservation du capital. "
            "Diversification maximale, faible concentration, faible volatilité."
        ),
        RiskProfile.MODERE: (
            "Profil modéré : équilibre entre rendement et risque. "
            "Concentration modérée, volatilité maîtrisée."
        ),
        RiskProfile.AGRESSIF: (
            "Profil agressif : recherche de rendement maximal. "
            "Concentration élevée sur les actifs à fort potentiel, "
            "tolérance élevée au drawdown."
        ),
    }
    return descs[profile]
