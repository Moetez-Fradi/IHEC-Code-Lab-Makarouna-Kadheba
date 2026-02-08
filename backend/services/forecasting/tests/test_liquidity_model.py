"""
Tests for LiquidityModel — hybrid price-direction + liquidity-regime model.

Covers:
  - Default & custom config
  - fit() returns expected metric keys, sets _is_fitted, populates _stats
  - predict() without order_book (defaults)
  - predict() with order_book
  - predict() without fit (unfitted, uses zero-mean stats)
  - Direction probabilities sum to ~1.0
  - Liquidity probabilities sum to ~1.0
  - Bullish OHLCV → higher price_up_prob
  - Bearish OHLCV → higher price_down_prob
  - High spread → lower liquidity
  - High depth  → higher liquidity
  - Extreme values don't crash (_sigmoid clipping)
"""

import numpy as np
import pytest

from backend.services.forecasting.models.liquidity_model import (
    LiquidityModel,
    LiquidityModelConfig,
    LiquidityPrediction,
)


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def model():
    return LiquidityModel()


@pytest.fixture
def fitted_model():
    m = LiquidityModel()
    prices = np.array([100.0 + i * 0.5 for i in range(60)])
    ob_series = [{"spread": 0.5, "depth": 10000, "imbalance": 0.0} for _ in range(60)]
    m.fit(prices, ob_series)
    return m


@pytest.fixture
def bullish_ohlcv():
    return {"open": 100.0, "high": 108.0, "low": 99.0, "close": 107.0, "volume": 8000}


@pytest.fixture
def bearish_ohlcv():
    return {"open": 107.0, "high": 108.0, "low": 99.0, "close": 100.0, "volume": 8000}


@pytest.fixture
def flat_ohlcv():
    return {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 3000}


# ── Config ────────────────────────────────────────────────────────────

class TestLiquidityModelConfig:
    def test_defaults(self):
        cfg = LiquidityModelConfig()
        assert cfg.spread_weight == 0.4
        assert cfg.depth_weight == 0.3
        assert cfg.imbalance_weight == 0.3

    def test_custom(self):
        cfg = LiquidityModelConfig(spread_weight=0.5, depth_weight=0.3, imbalance_weight=0.2)
        assert cfg.spread_weight == 0.5


# ── Fit ───────────────────────────────────────────────────────────────

class TestFit:
    def test_fit_returns_metrics(self, model):
        prices = np.array([100.0 + i for i in range(60)])
        obs = [{"spread": 0.3, "depth": 5000} for _ in range(60)]
        metrics = model.fit(prices, obs)
        assert "loss" in metrics
        assert "accuracy_direction" in metrics
        assert "auc_liquidity" in metrics

    def test_fit_sets_flag(self, model):
        assert not model._is_fitted
        prices = np.array([100.0 + i for i in range(60)])
        obs = [{"spread": 0.3} for _ in range(60)]
        model.fit(prices, obs)
        assert model._is_fitted

    def test_fit_populates_stats(self, model):
        prices = np.array([100.0 + i for i in range(60)])
        obs = [{"spread": 0.3, "depth": 5000} for _ in range(60)]
        model.fit(prices, obs)
        assert "mean_spread" in model._stats
        assert "std_spread" in model._stats
        assert "mean_depth" in model._stats
        assert "std_depth" in model._stats
        assert "mean_return" in model._stats

    def test_fit_stats_values(self, model):
        prices = np.array([100.0] * 60)
        obs = [{"spread": 1.0, "depth": 2000} for _ in range(60)]
        model.fit(prices, obs)
        assert model._stats["mean_spread"] == pytest.approx(1.0)
        assert model._stats["mean_depth"] == pytest.approx(2000.0)


# ── Predict ───────────────────────────────────────────────────────────

class TestPredict:
    def test_predict_returns_dataclass(self, model, flat_ohlcv):
        pred = model.predict(flat_ohlcv)
        assert isinstance(pred, LiquidityPrediction)

    def test_predict_no_order_book(self, model, flat_ohlcv):
        pred = model.predict(flat_ohlcv)
        assert 0.0 <= pred.liquidity_high_prob <= 1.0
        assert 0.0 <= pred.liquidity_low_prob <= 1.0

    def test_predict_with_order_book(self, fitted_model, flat_ohlcv):
        ob = {"spread": 0.5, "depth": 10000, "imbalance": 0.05}
        pred = fitted_model.predict(flat_ohlcv, order_book=ob)
        assert isinstance(pred, LiquidityPrediction)

    def test_direction_probs_sum_to_one(self, fitted_model, bullish_ohlcv):
        pred = fitted_model.predict(bullish_ohlcv, {"spread": 0.5, "depth": 10000})
        total = pred.price_up_prob + pred.price_flat_prob + pred.price_down_prob
        assert total == pytest.approx(1.0, abs=0.01)

    def test_liquidity_probs_sum_to_one(self, fitted_model, flat_ohlcv):
        pred = fitted_model.predict(flat_ohlcv, {"spread": 0.5, "depth": 10000})
        assert pred.liquidity_high_prob + pred.liquidity_low_prob == pytest.approx(1.0, abs=0.01)

    def test_bullish_has_higher_up_prob(self, fitted_model, bullish_ohlcv, bearish_ohlcv):
        ob = {"spread": 0.5, "depth": 10000}
        bull = fitted_model.predict(bullish_ohlcv, ob)
        bear = fitted_model.predict(bearish_ohlcv, ob)
        assert bull.price_up_prob > bear.price_up_prob

    def test_bearish_has_higher_down_prob(self, fitted_model, bullish_ohlcv, bearish_ohlcv):
        ob = {"spread": 0.5, "depth": 10000}
        bull = fitted_model.predict(bullish_ohlcv, ob)
        bear = fitted_model.predict(bearish_ohlcv, ob)
        assert bear.price_down_prob > bull.price_down_prob

    def test_high_spread_lowers_liquidity(self, fitted_model, flat_ohlcv):
        low_spread = fitted_model.predict(flat_ohlcv, {"spread": 0.1, "depth": 10000})
        high_spread = fitted_model.predict(flat_ohlcv, {"spread": 5.0, "depth": 10000})
        assert low_spread.liquidity_high_prob > high_spread.liquidity_high_prob

    def test_high_depth_raises_liquidity(self, fitted_model, flat_ohlcv):
        low_depth = fitted_model.predict(flat_ohlcv, {"spread": 0.5, "depth": 100})
        high_depth = fitted_model.predict(flat_ohlcv, {"spread": 0.5, "depth": 100000})
        assert high_depth.liquidity_high_prob > low_depth.liquidity_high_prob

    def test_extreme_values_no_crash(self, model):
        extreme = {"open": 1e12, "high": 1e12, "low": 0.0001, "close": 1e12, "volume": 0}
        pred = model.predict(extreme, {"spread": 1e9, "depth": 0, "imbalance": -1e6})
        assert 0.0 <= pred.liquidity_high_prob <= 1.0
        assert 0.0 <= pred.price_up_prob <= 1.0

    def test_all_probs_in_valid_range(self, fitted_model, bullish_ohlcv):
        pred = fitted_model.predict(bullish_ohlcv, {"spread": 0.5, "depth": 10000})
        for val in [pred.price_up_prob, pred.price_flat_prob, pred.price_down_prob,
                    pred.liquidity_high_prob, pred.liquidity_low_prob]:
            assert 0.0 <= val <= 1.0
