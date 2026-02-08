"""Portfolio performance metrics."""

import numpy as np

from app.core.config import settings


def sharpe_ratio(returns: np.ndarray, rf: float | None = None) -> float:
    rf = rf if rf is not None else settings.RISK_FREE_RATE
    daily_rf = rf / 252
    excess = returns - daily_rf
    std = excess.std()
    if std < 1e-10:
        return 0.0
    return float(np.mean(excess) / std * np.sqrt(252))


def sortino_ratio(returns: np.ndarray, rf: float | None = None) -> float:
    rf = rf if rf is not None else settings.RISK_FREE_RATE
    daily_rf = rf / 252
    excess = returns - daily_rf
    downside = np.minimum(excess, 0)
    down_std = np.std(downside)
    if down_std == 0:
        return 0.0
    return float(np.mean(excess) / down_std * np.sqrt(252))


def max_drawdown(returns: np.ndarray) -> float:
    cum = np.cumprod(1 + returns)
    peak = np.maximum.accumulate(cum)
    dd = (cum - peak) / peak
    return float(np.min(dd))


def annual_volatility(returns: np.ndarray) -> float:
    return float(np.std(returns) * np.sqrt(252))


def total_return(returns: np.ndarray) -> float:
    return float(np.prod(1 + returns) - 1)


def compute_all(returns: np.ndarray) -> dict:
    return {
        "sharpe": sharpe_ratio(returns),
        "sortino": sortino_ratio(returns),
        "max_drawdown": max_drawdown(returns),
        "volatility": annual_volatility(returns),
        "total_return": total_return(returns),
    }
