"""
Reward functions used by the RL environments.

Keeping them in a separate file makes it easy to experiment
with different reward shaping strategies.
"""

import numpy as np


def defender_reward(
    portfolio_return: float,
    volatility: float,
    stress: float,
) -> float:
    """Reward for Agent B (portfolio optimiser).

    Maximise a Sharpe‑like ratio while penalising drawdown
    and exposure to ongoing stress.
    """
    sharpe = portfolio_return / (volatility + 1e-6)
    drawdown_penalty = -max(0.0, -portfolio_return)
    stress_penalty = -stress * 0.1
    return sharpe + drawdown_penalty + stress_penalty


def adversary_reward(
    value_before: float,
    value_after: float,
) -> float:
    """Reward for Agent A (stress tester).

    Proportional to the loss inflicted on the portfolio.
    """
    return (value_before - value_after) / (value_before + 1e-8)
