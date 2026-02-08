"""Tests for portfolio tracker, metrics, profile adjuster, and simulator."""

import numpy as np
import pytest

from app.portfolio.metrics import (
    sharpe_ratio, sortino_ratio, max_drawdown,
    annual_volatility, total_return, compute_all,
)
from app.portfolio.tracker import Portfolio
from app.portfolio.profile import adjust_weights, profile_description
from app.portfolio.simulator import simulate
from app.core.types import RiskProfile


class TestMetrics:
    def _returns(self, n=252):
        return np.random.randn(n) * 0.01 + 0.0003

    def test_sharpe_positive(self):
        rets = self._returns()
        s = sharpe_ratio(rets)
        assert isinstance(s, float)

    def test_sharpe_zero_vol(self):
        assert sharpe_ratio(np.zeros(100)) == 0.0

    def test_sortino_positive(self):
        rets = self._returns()
        s = sortino_ratio(rets)
        assert isinstance(s, float)

    def test_max_drawdown_negative(self):
        rets = self._returns()
        dd = max_drawdown(rets)
        assert dd <= 0.0

    def test_annual_volatility_positive(self):
        rets = self._returns()
        vol = annual_volatility(rets)
        assert vol > 0

    def test_compute_all_keys(self):
        result = compute_all(self._returns())
        assert set(result.keys()) == {"sharpe", "sortino", "max_drawdown", "volatility", "total_return"}


class TestPortfolio:
    def test_initial_value(self):
        p = Portfolio(tickers=["A", "B"], cash=100_000)
        prices = np.array([50.0, 100.0])
        assert p.value(prices) == 100_000

    def test_rebalance_changes_holdings(self):
        p = Portfolio(tickers=["A", "B"], cash=100_000)
        prices = np.array([50.0, 100.0])
        weights = np.array([0.6, 0.4])
        p.rebalance(weights, prices, step=0)
        assert len(p.holdings) > 0
        assert len(p.history) > 0

    def test_snapshot_structure(self):
        p = Portfolio(tickers=["A", "B"], cash=100_000)
        prices = np.array([50.0, 100.0])
        snap = p.snapshot(prices)
        assert "cash" in snap
        assert "value" in snap
        assert "weights" in snap
        assert "n_transactions" in snap

    def test_value_after_rebalance(self):
        p = Portfolio(tickers=["A"], cash=10_000)
        prices = np.array([100.0])
        p.rebalance(np.array([1.0]), prices, step=0)
        # Value should be close to initial (minus tx cost)
        assert p.value(prices) < 10_000  # tx cost deducted
        assert p.value(prices) > 9_900   # not too much lost


class TestProfileAdjuster:
    def test_conservateur_caps_weights(self):
        raw = np.array([0.5, 0.3, 0.2])
        adj = adjust_weights(raw, RiskProfile.CONSERVATEUR)
        assert all(w <= 0.16 for w in adj)

    def test_agressif_preserves_high(self):
        raw = np.array([0.6, 0.3, 0.1])
        adj = adjust_weights(raw, RiskProfile.AGRESSIF)
        assert adj[0] > 0.3  # still concentrated

    def test_modere_middle_ground(self):
        raw = np.array([0.4, 0.4, 0.2])
        adj = adjust_weights(raw, RiskProfile.MODERE)
        assert all(w <= 0.26 for w in adj)
        assert adj.sum() <= 1.0 + 1e-9

    def test_profile_description_returns_string(self):
        for p in RiskProfile:
            desc = profile_description(p)
            assert isinstance(desc, str)
            assert len(desc) > 10


class TestSimulator:
    def _prices(self, n=100, assets=3):
        base = np.full(assets, 50.0)
        prices = [base]
        for _ in range(n - 1):
            ret = 1 + np.random.randn(assets) * 0.02
            prices.append(prices[-1] * ret)
        return np.array(prices)

    def test_simulate_returns_keys(self):
        w = np.array([0.4, 0.3, 0.3])
        result = simulate(w, self._prices())
        for key in ("roi", "sharpe", "max_drawdown", "daily_values", "final_value"):
            assert key in result

    def test_simulate_with_days(self):
        result = simulate(np.array([0.5, 0.5, 0.0]), self._prices(200), days=50)
        assert result["n_days"] == 49  # diff loses one row

    def test_simulate_equity_length(self):
        result = simulate(np.array([1 / 3] * 3), self._prices(60))
        assert len(result["daily_values"]) == 60  # n_days + 1
