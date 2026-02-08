"""
Normalisation helpers consumed by the RL environment.
"""

import numpy as np


def minmax(arr: np.ndarray) -> np.ndarray:
    lo, hi = arr.min(), arr.max()
    return (arr - lo) / (hi - lo + 1e-8)


def zscore(arr: np.ndarray) -> np.ndarray:
    return (arr - arr.mean()) / (arr.std() + 1e-8)


def build_state_vector(
    weights: np.ndarray,
    prices: np.ndarray,
    volatilities: np.ndarray,
    macro: dict[str, float],
    stress: float = 0.0,
) -> np.ndarray:
    """Concatenate and normalise all features into a single vector."""
    norm_w = weights / (weights.sum() + 1e-8)
    norm_p = minmax(prices)
    norm_v = minmax(volatilities)
    macro_arr = zscore(np.array(list(macro.values()), dtype=np.float32))
    return np.concatenate([norm_w, norm_p, norm_v, macro_arr, [stress]]).astype(
        np.float32
    )
