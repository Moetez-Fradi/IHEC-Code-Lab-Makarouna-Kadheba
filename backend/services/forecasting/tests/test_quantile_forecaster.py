"""
Tests for QuantileForecaster — probabilistic quantile price forecasting.

Covers:
  - Default & custom config
  - fit() success, metrics keys, sets _is_fitted
  - fit() with too-short series raises ValueError
  - predict() unfitted (derives stats from input)
  - predict() after fit (uses stored weights)
  - predict() horizon 1–5 produces correct number of QuantilePredictions
  - predict() quantile ordering: p10 < p50 < p90
  - predict() invalid horizon raises ValueError
  - save / load round-trip preserves weights
  - pinball_loss static method correctness
"""

import os
import tempfile

import numpy as np
import pytest

from backend.services.forecasting.models.quantile_forecaster import (
    QuantileForecaster,
    QuantileForecasterConfig,
    QuantilePrediction,
    QUANTILES,
    MAX_HORIZON,
)


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def price_series():
    """60-point synthetic price series (slight uptrend + noise)."""
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 59)
    prices = 100.0 * np.exp(np.concatenate([[0], np.cumsum(returns)]))
    return prices


@pytest.fixture
def short_series():
    """Series too short for default config (seq_len=30 + max_horizon=5 = 35)."""
    return np.array([100.0 + i for i in range(20)])


@pytest.fixture
def forecaster():
    return QuantileForecaster()


@pytest.fixture
def fitted_forecaster(forecaster, price_series):
    forecaster.fit(price_series)
    return forecaster


# ── Config ────────────────────────────────────────────────────────────

class TestQuantileForecasterConfig:
    def test_default_config(self):
        cfg = QuantileForecasterConfig()
        assert cfg.seq_len == 30
        assert cfg.max_horizon == MAX_HORIZON
        assert cfg.quantiles == QUANTILES
        assert cfg.epochs == 50

    def test_custom_config(self):
        cfg = QuantileForecasterConfig(seq_len=10, epochs=5, max_horizon=3)
        assert cfg.seq_len == 10
        assert cfg.epochs == 5
        assert cfg.max_horizon == 3


# ── Fit ───────────────────────────────────────────────────────────────

class TestFit:
    def test_fit_returns_metrics(self, forecaster, price_series):
        metrics = forecaster.fit(price_series)
        assert "pinball_loss_q10" in metrics
        assert "pinball_loss_q50" in metrics
        assert "pinball_loss_q90" in metrics
        assert "epochs" in metrics
        assert metrics["epochs"] == forecaster.config.epochs

    def test_fit_sets_fitted_flag(self, forecaster, price_series):
        assert not forecaster._is_fitted
        forecaster.fit(price_series)
        assert forecaster._is_fitted

    def test_fit_stores_weights(self, forecaster, price_series):
        forecaster.fit(price_series)
        assert "mu" in forecaster._weights
        assert "sigma" in forecaster._weights
        assert "last_price" in forecaster._weights

    def test_fit_too_short_raises(self, forecaster, short_series):
        with pytest.raises(ValueError, match="Need at least"):
            forecaster.fit(short_series)

    def test_fit_with_feature_matrix(self, forecaster, price_series):
        features = np.random.rand(len(price_series), 3)
        metrics = forecaster.fit(price_series, feature_matrix=features)
        assert forecaster._is_fitted
        assert "pinball_loss_q50" in metrics

    def test_fit_pinball_loss_range(self, forecaster, price_series):
        metrics = forecaster.fit(price_series)
        assert 0.0 < metrics["pinball_loss_q10"] <= 0.05
        assert 0.0 < metrics["pinball_loss_q50"] <= 0.03
        assert 0.0 < metrics["pinball_loss_q90"] <= 0.05


# ── Predict ───────────────────────────────────────────────────────────

class TestPredict:
    def test_predict_unfitted_single_horizon(self, forecaster, price_series):
        recent = price_series[-30:]
        preds = forecaster.predict(recent, horizon=1)
        assert len(preds) == 1
        assert isinstance(preds[0], QuantilePrediction)
        assert preds[0].horizon_day == 1

    def test_predict_fitted_single_horizon(self, fitted_forecaster, price_series):
        recent = price_series[-30:]
        preds = fitted_forecaster.predict(recent, horizon=1)
        assert len(preds) == 1

    def test_predict_multi_horizon(self, fitted_forecaster, price_series):
        recent = price_series[-30:]
        for h in range(1, MAX_HORIZON + 1):
            preds = fitted_forecaster.predict(recent, horizon=h)
            assert len(preds) == h
            for i, p in enumerate(preds):
                assert p.horizon_day == i + 1

    def test_predict_quantile_ordering(self, fitted_forecaster, price_series):
        """p10 <= p50 <= p90 for every horizon step."""
        recent = price_series[-30:]
        preds = fitted_forecaster.predict(recent, horizon=5)
        for p in preds:
            assert p.p10 <= p.p50 <= p.p90

    def test_predict_values_near_last_price(self, fitted_forecaster, price_series):
        """1-day forecast should be reasonably close to last price."""
        recent = price_series[-30:]
        preds = fitted_forecaster.predict(recent, horizon=1)
        last = recent[-1]
        assert abs(preds[0].p50 - last) / last < 0.10  # within 10 %

    def test_predict_invalid_horizon_zero(self, forecaster, price_series):
        with pytest.raises(ValueError):
            forecaster.predict(price_series[-30:], horizon=0)

    def test_predict_invalid_horizon_too_large(self, forecaster, price_series):
        with pytest.raises(ValueError):
            forecaster.predict(price_series[-30:], horizon=MAX_HORIZON + 1)

    def test_predict_with_features_dict(self, fitted_forecaster, price_series):
        recent = price_series[-30:]
        preds = fitted_forecaster.predict(
            recent, features={"close": 100, "volume": 5000}, horizon=1
        )
        assert len(preds) == 1

    def test_predict_spread_grows_with_horizon(self, fitted_forecaster, price_series):
        """The p90-p10 spread should generally increase for longer horizons."""
        recent = price_series[-30:]
        preds = fitted_forecaster.predict(recent, horizon=5)
        spreads = [p.p90 - p.p10 for p in preds]
        # Spread at day 5 should be >= spread at day 1
        assert spreads[-1] >= spreads[0]


# ── Save / Load ───────────────────────────────────────────────────────

class TestPersistence:
    def test_save_load_round_trip(self, fitted_forecaster, price_series):
        recent = price_series[-30:]
        preds_before = fitted_forecaster.predict(recent, horizon=3)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "model.npz")
            fitted_forecaster.save(path)

            new_fc = QuantileForecaster()
            new_fc.load(path)

        assert new_fc._is_fitted
        preds_after = new_fc.predict(recent, horizon=3)

        for a, b in zip(preds_before, preds_after):
            assert a.p10 == pytest.approx(b.p10, rel=1e-6)
            assert a.p50 == pytest.approx(b.p50, rel=1e-6)
            assert a.p90 == pytest.approx(b.p90, rel=1e-6)


# ── Pinball loss ──────────────────────────────────────────────────────

class TestPinballLoss:
    def test_pinball_loss_perfect_prediction(self):
        y = np.array([100.0, 200.0, 300.0])
        loss = QuantileForecaster.pinball_loss(y, y, 0.5)
        assert loss == pytest.approx(0.0)

    def test_pinball_loss_under_prediction(self):
        y_true = np.array([110.0])
        y_pred = np.array([100.0])
        loss_50 = QuantileForecaster.pinball_loss(y_true, y_pred, 0.5)
        loss_90 = QuantileForecaster.pinball_loss(y_true, y_pred, 0.9)
        # Under-predicting is penalised more at higher quantiles
        assert loss_90 > loss_50

    def test_pinball_loss_over_prediction(self):
        y_true = np.array([90.0])
        y_pred = np.array([100.0])
        loss_10 = QuantileForecaster.pinball_loss(y_true, y_pred, 0.1)
        loss_50 = QuantileForecaster.pinball_loss(y_true, y_pred, 0.5)
        # Over-predicting is penalised more at lower quantiles
        assert loss_10 > loss_50

    def test_pinball_loss_non_negative(self):
        y_true = np.array([100.0, 105.0, 95.0])
        y_pred = np.array([102.0, 98.0, 97.0])
        for q in [0.1, 0.5, 0.9]:
            loss = QuantileForecaster.pinball_loss(y_true, y_pred, q)
            assert loss >= 0.0
