"""Agent A – Adversarial stress tester."""

import logging

import numpy as np

from app.core.types import StressType

logger = logging.getLogger(__name__)

_SYSTEMIC = [StressType.LIQUIDITY_SHOCK, StressType.INTEREST_RATE_SPIKE, StressType.CURRENCY_DEPRECIATION]


class Adversary:
    """Heuristic adversarial agent.

    Inspects the portfolio state and picks the stress scenario
    most likely to cause damage.  In a full implementation this
    would be replaced by a learned SAC policy.
    """

    def generate(self, state: np.ndarray, n_assets: int) -> dict:
        weights = state[:n_assets]
        max_w = float(np.max(weights))

        if max_w > 0.30:
            kind = StressType.SECTOR_CRASH
            intensity = float(np.random.uniform(0.10, 0.30))
        else:
            kind = _SYSTEMIC[np.random.randint(len(_SYSTEMIC))]
            intensity = float(np.random.uniform(0.05, 0.20))

        return {"type": kind, "intensity": intensity}
