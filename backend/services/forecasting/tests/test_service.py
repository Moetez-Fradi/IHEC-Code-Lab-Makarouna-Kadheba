"""
Tests for ForecastingService — the orchestrator wiring all sub-modules.

Covers:
  - predict(): returns ForecastOutput with correct structure
  - predict(): multi-horizon
  - predict(): with and without history
  - predict(): with and without order_book
  - explain_forecast(): returns ExplainOutput with CI, SHAP, drivers
  - recommend_execution(): returns RecommendOutput with valid signal
  - augment(): returns AugmentOutput with correct counts
  - augment(): different methods
  - transfer_learn(): returns TransferLearnOutput, swaps model
"""

import numpy as np
import pytest

from backend.services.forecasting.service import ForecastingService
from backend.services.forecasting.schemas import (
    ForecastOutput,
    ExplainOutput,
    RecommendOutput,
    AugmentOutput,
    TransferLearnOutput,
    QuantileStep,
    DriverDetail,
)


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def svc():
    return ForecastingService()


@pytest.fixture
def base_features():
    return {
        "security_id": "BIAT",
        "date": "2026-02-08",
        "ohlcv": {"open": 100, "high": 102, "low": 99, "close": 101, "volume": 5000},
        "order_book": {"spread": 0.5, "depth": 12000, "imbalance": 0.1},
        "sector": "banking",
        "news": ["BIAT Q4 results"],
        "indicators": {"rsi": 55},
        "horizon": 1,
        "history": [98 + i * 0.1 for i in range(40)],
    }


@pytest.fixture
def minimal_features():
    return {
        "security_id": "X",
        "date": "2026-01-01",
        "ohlcv": {"open": 50, "high": 51, "low": 49, "close": 50, "volume": 1000},
    }


# ── predict ───────────────────────────────────────────────────────────

class TestPredict:
    def test_returns_forecast_output(self, svc, base_features):
        out = svc.predict(base_features)
        assert isinstance(out, ForecastOutput)

    def test_quantile_count_matches_horizon(self, svc, base_features):
        for h in [1, 2, 3, 5]:
            base_features["horizon"] = h
            out = svc.predict(base_features)
            assert len(out.quantiles) == h
            assert out.horizon_days == h

    def test_quantile_step_type(self, svc, base_features):
        out = svc.predict(base_features)
        for q in out.quantiles:
            assert isinstance(q, QuantileStep)
            assert q.p10 <= q.p50 <= q.p90

    def test_liquidity_probs(self, svc, base_features):
        out = svc.predict(base_features)
        assert 0.0 <= out.liquidity_high_prob <= 1.0
        assert 0.0 <= out.liquidity_low_prob <= 1.0
        assert out.liquidity_high_prob + out.liquidity_low_prob == pytest.approx(1.0, abs=0.01)

    def test_direction_probs(self, svc, base_features):
        out = svc.predict(base_features)
        assert 0.0 <= out.price_up_prob <= 1.0
        assert 0.0 <= out.price_down_prob <= 1.0

    def test_predict_without_history(self, svc, minimal_features):
        out = svc.predict(minimal_features)
        assert isinstance(out, ForecastOutput)
        assert len(out.quantiles) == 1  # default horizon=1

    def test_predict_without_order_book(self, svc, minimal_features):
        out = svc.predict(minimal_features)
        assert 0.0 <= out.liquidity_high_prob <= 1.0

    def test_predict_default_horizon(self, svc, minimal_features):
        out = svc.predict(minimal_features)
        assert out.horizon_days == 1


# ── explain_forecast ──────────────────────────────────────────────────

class TestExplainForecast:
    def test_returns_explain_output(self, svc, base_features):
        out = svc.explain_forecast(base_features)
        assert isinstance(out, ExplainOutput)

    def test_confidence_interval_two_elements(self, svc, base_features):
        out = svc.explain_forecast(base_features)
        assert len(out.confidence_interval) == 2
        assert out.confidence_interval[0] < out.confidence_interval[1]

    def test_shap_values_present(self, svc, base_features):
        out = svc.explain_forecast(base_features)
        assert len(out.shap_values) > 0
        # Should include merged OHLCV + order_book + indicators keys
        assert "close" in out.shap_values
        assert "volume" in out.shap_values

    def test_top_drivers_are_driver_detail(self, svc, base_features):
        out = svc.explain_forecast(base_features)
        assert len(out.top_drivers) > 0
        for d in out.top_drivers:
            assert isinstance(d, DriverDetail)
            assert d.direction in ("positive", "negative")

    def test_top_drivers_limited_to_5(self, svc, base_features):
        out = svc.explain_forecast(base_features)
        assert len(out.top_drivers) <= 5

    def test_explain_without_optional_fields(self, svc, minimal_features):
        out = svc.explain_forecast(minimal_features)
        assert isinstance(out, ExplainOutput)
        assert len(out.confidence_interval) == 2


# ── recommend_execution ──────────────────────────────────────────────

class TestRecommendExecution:
    def test_returns_recommend_output(self, svc, base_features):
        out = svc.recommend_execution(base_features)
        assert isinstance(out, RecommendOutput)

    def test_signal_in_valid_set(self, svc, base_features):
        out = svc.recommend_execution(base_features)
        assert out.signal in {"enter", "exit", "hold", "defer"}

    def test_confidence_in_range(self, svc, base_features):
        out = svc.recommend_execution(base_features)
        assert 0.0 <= out.confidence <= 1.0

    def test_timing_present(self, svc, base_features):
        out = svc.recommend_execution(base_features)
        assert out.timing in {
            "intraday", "next_open", "next_close", "wait_1_day"
        }

    def test_reason_not_empty(self, svc, base_features):
        out = svc.recommend_execution(base_features)
        assert len(out.reason) > 0

    def test_details_dict_keys(self, svc, base_features):
        out = svc.recommend_execution(base_features)
        assert "upside_pct" in out.details
        assert "spread_frac_pct" in out.details
        assert "liq_high_prob" in out.details

    def test_recommend_without_optional(self, svc, minimal_features):
        out = svc.recommend_execution(minimal_features)
        assert out.signal in {"enter", "exit", "hold", "defer"}


# ── augment ───────────────────────────────────────────────────────────

class TestAugment:
    def test_returns_augment_output(self, svc):
        out = svc.augment(
            price_history=[100 + i * 0.5 for i in range(60)],
            n_synthetic=3,
        )
        assert isinstance(out, AugmentOutput)

    def test_correct_count(self, svc):
        out = svc.augment(
            price_history=[100 + i * 0.5 for i in range(60)],
            n_synthetic=7,
        )
        assert out.n_generated == 7

    def test_sample_series_capped_at_3(self, svc):
        out = svc.augment(
            price_history=[100 + i * 0.5 for i in range(60)],
            n_synthetic=10,
        )
        assert len(out.sample_series) <= 3

    def test_method_vae(self, svc):
        out = svc.augment(
            price_history=[100 + i for i in range(60)],
            method="vae",
        )
        assert out.method == "vae"

    def test_method_gan(self, svc):
        out = svc.augment(
            price_history=[100 + i for i in range(60)],
            method="gan",
        )
        assert out.method == "gan"

    def test_sample_series_are_lists_of_floats(self, svc):
        out = svc.augment(
            price_history=[100 + i for i in range(60)],
            n_synthetic=2,
        )
        for series in out.sample_series:
            assert isinstance(series, list)
            for val in series:
                assert isinstance(val, float)


# ── transfer_learn ────────────────────────────────────────────────────

class TestTransferLearn:
    def test_returns_transfer_learn_output(self, svc):
        out = svc.transfer_learn(
            target_prices=[45 + i * 0.1 for i in range(60)],
            source_corpus={
                "BIAT": [100 + i * 0.5 for i in range(60)],
                "BH": [20 + i * 0.2 for i in range(60)],
            },
        )
        assert isinstance(out, TransferLearnOutput)

    def test_flags_set(self, svc):
        out = svc.transfer_learn(
            target_prices=[45 + i * 0.1 for i in range(60)],
            source_corpus={
                "A": [100 + i for i in range(60)],
            },
        )
        assert out.pretrained is True
        assert out.finetuned is True

    def test_pretrain_sources_count(self, svc):
        out = svc.transfer_learn(
            target_prices=[45 + i * 0.1 for i in range(60)],
            source_corpus={
                "A": [100 + i for i in range(60)],
                "B": [50 + i for i in range(60)],
                "C": [30 + i for i in range(60)],
            },
        )
        assert out.pretrain_sources == 3

    def test_metrics_present(self, svc):
        out = svc.transfer_learn(
            target_prices=[45 + i * 0.1 for i in range(60)],
            source_corpus={"X": [100 + i for i in range(60)]},
        )
        assert "pinball_loss_q50" in out.metrics

    def test_swaps_forecaster(self, svc):
        original_forecaster = svc.quantile_forecaster
        svc.transfer_learn(
            target_prices=[45 + i * 0.1 for i in range(60)],
            source_corpus={"X": [100 + i for i in range(60)]},
        )
        assert svc.quantile_forecaster is not original_forecaster
        assert svc.quantile_forecaster._is_fitted
