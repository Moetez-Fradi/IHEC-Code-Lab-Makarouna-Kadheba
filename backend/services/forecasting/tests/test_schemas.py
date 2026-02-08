"""
Tests for Pydantic schemas — request / response model validation.

Covers:
  - FeatureInput validation (required fields, defaults, constraints)
  - AugmentRequest constraints (n_synthetic bounds)
  - TransferLearnRequest required fields
  - Response models can be instantiated with valid data
"""

import pytest
from pydantic import ValidationError

from backend.services.forecasting.schemas import (
    FeatureInput,
    AugmentRequest,
    TransferLearnRequest,
    QuantileStep,
    ForecastOutput,
    ExplainOutput,
    RecommendOutput,
    AugmentOutput,
    TransferLearnOutput,
    DriverDetail,
)


# ── FeatureInput ──────────────────────────────────────────────────────

class TestFeatureInput:
    def test_valid_minimal(self):
        fi = FeatureInput(
            security_id="X",
            date="2026-01-01",
            ohlcv={"open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100},
        )
        assert fi.security_id == "X"
        assert fi.horizon == 1  # default
        assert fi.order_book is None
        assert fi.history is None

    def test_valid_full(self):
        fi = FeatureInput(
            security_id="BIAT",
            date="2026-02-08",
            ohlcv={"open": 100, "high": 102, "low": 99, "close": 101, "volume": 5000},
            order_book={"spread": 0.5, "depth": 12000},
            sector="banking",
            news=["headline"],
            indicators={"rsi": 55},
            horizon=5,
            history=[100.0] * 40,
        )
        assert fi.horizon == 5
        assert len(fi.history) == 40

    def test_missing_security_id(self):
        with pytest.raises(ValidationError):
            FeatureInput(
                date="2026-01-01",
                ohlcv={"open": 1, "high": 2, "low": 0.5, "close": 1, "volume": 10},
            )

    def test_missing_date(self):
        with pytest.raises(ValidationError):
            FeatureInput(
                security_id="X",
                ohlcv={"open": 1, "high": 2, "low": 0.5, "close": 1, "volume": 10},
            )

    def test_missing_ohlcv(self):
        with pytest.raises(ValidationError):
            FeatureInput(security_id="X", date="2026-01-01")

    def test_horizon_ge_1(self):
        with pytest.raises(ValidationError):
            FeatureInput(
                security_id="X",
                date="2026-01-01",
                ohlcv={"open": 1, "high": 2, "low": 0.5, "close": 1, "volume": 10},
                horizon=0,
            )

    def test_horizon_le_5(self):
        with pytest.raises(ValidationError):
            FeatureInput(
                security_id="X",
                date="2026-01-01",
                ohlcv={"open": 1, "high": 2, "low": 0.5, "close": 1, "volume": 10},
                horizon=6,
            )


# ── AugmentRequest ───────────────────────────────────────────────────

class TestAugmentRequest:
    def test_valid(self):
        ar = AugmentRequest(
            security_id="X",
            price_history=[100 + i for i in range(10)],
            n_synthetic=5,
            method="vae",
        )
        assert ar.n_synthetic == 5

    def test_n_synthetic_ge_1(self):
        with pytest.raises(ValidationError):
            AugmentRequest(
                security_id="X",
                price_history=[100],
                n_synthetic=0,
            )

    def test_n_synthetic_le_50(self):
        with pytest.raises(ValidationError):
            AugmentRequest(
                security_id="X",
                price_history=[100],
                n_synthetic=51,
            )

    def test_missing_price_history(self):
        with pytest.raises(ValidationError):
            AugmentRequest(security_id="X")

    def test_defaults(self):
        ar = AugmentRequest(
            security_id="X",
            price_history=[100, 101],
        )
        assert ar.n_synthetic == 5
        assert ar.method == "vae"


# ── TransferLearnRequest ─────────────────────────────────────────────

class TestTransferLearnRequest:
    def test_valid(self):
        tlr = TransferLearnRequest(
            target_security_id="X",
            target_prices=[100, 101, 102],
            source_corpus={"A": [10, 11, 12]},
        )
        assert tlr.target_security_id == "X"

    def test_missing_target_prices(self):
        with pytest.raises(ValidationError):
            TransferLearnRequest(
                target_security_id="X",
                source_corpus={"A": [10]},
            )

    def test_missing_source_corpus(self):
        with pytest.raises(ValidationError):
            TransferLearnRequest(
                target_security_id="X",
                target_prices=[100],
            )


# ── Response models ──────────────────────────────────────────────────

class TestResponseSchemas:
    def test_quantile_step(self):
        qs = QuantileStep(horizon_day=1, p10=98.0, p50=100.0, p90=102.0)
        assert qs.p10 < qs.p50 < qs.p90

    def test_forecast_output(self):
        fo = ForecastOutput(
            quantiles=[QuantileStep(horizon_day=1, p10=98, p50=100, p90=102)],
            liquidity_high_prob=0.7,
            liquidity_low_prob=0.3,
            price_up_prob=0.6,
            price_down_prob=0.3,
            horizon_days=1,
        )
        assert fo.horizon_days == 1

    def test_driver_detail(self):
        dd = DriverDetail(feature="volume", label="Trading volume", shap_value=10.0, direction="positive")
        assert dd.direction == "positive"

    def test_explain_output(self):
        eo = ExplainOutput(
            confidence_interval=[95.0, 105.0],
            shap_values={"volume": 10.0},
            top_drivers=[DriverDetail(feature="volume", label="Trading volume", shap_value=10.0, direction="positive")],
        )
        assert len(eo.top_drivers) == 1

    def test_recommend_output(self):
        ro = RecommendOutput(
            signal="enter",
            confidence=0.8,
            reason="Looks good",
            timing="intraday",
            details={"upside_pct": 3.0},
        )
        assert ro.signal == "enter"

    def test_augment_output(self):
        ao = AugmentOutput(
            n_generated=5,
            method="vae",
            sample_series=[[100.0, 101.0], [99.0, 100.0]],
        )
        assert ao.n_generated == 5

    def test_transfer_learn_output(self):
        tlo = TransferLearnOutput(
            pretrained=True,
            finetuned=True,
            pretrain_sources=3,
            frozen_layers=2,
            metrics={"loss": 0.1},
        )
        assert tlo.pretrained is True
