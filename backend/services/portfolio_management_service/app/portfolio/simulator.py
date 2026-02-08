"""Portfolio simulation — virtual capital, ROI, Sharpe, Max Drawdown."""

import numpy as np

from app.portfolio import metrics as pm
from app.core.config import settings


def simulate(
    weights: np.ndarray,
    price_matrix: np.ndarray,
    capital: float | None = None,
    days: int | None = None,
) -> dict:
    """Run a historical simulation of a fixed-weight portfolio.

    Parameters
    ----------
    weights : array of per-asset weights (sums ≤ 1)
    price_matrix : (T, n_assets) daily close prices
    capital : starting capital in TND (default from settings)
    days : how many trailing days to simulate (default: all)

    Returns
    -------
    dict with roi, sharpe, max_drawdown, sortino, volatility,
    daily_values list, and final_value.
    """
    capital = capital or settings.INITIAL_CAPITAL
    if days and days < price_matrix.shape[0]:
        price_matrix = price_matrix[-days:]

    returns = np.diff(price_matrix, axis=0) / price_matrix[:-1]
    port_returns = (returns * weights).sum(axis=1)

    # Build daily equity curve
    equity = [capital]
    for r in port_returns:
        equity.append(equity[-1] * (1 + r))

    met = pm.compute_all(port_returns)

    return {
        "initial_capital": capital,
        "final_value": round(equity[-1], 2),
        "roi": round(met["total_return"] * 100, 2),
        "sharpe": round(met["sharpe"], 4),
        "sortino": round(met["sortino"], 4),
        "max_drawdown": round(met["max_drawdown"] * 100, 2),
        "volatility": round(met["volatility"] * 100, 2),
        "n_days": len(port_returns),
        "daily_values": [round(v, 2) for v in equity],
    }
