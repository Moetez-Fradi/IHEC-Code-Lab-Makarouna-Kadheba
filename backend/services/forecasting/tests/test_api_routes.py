"""
Integration tests for the FastAPI routes (/api/forecasting/*).

Uses FastAPI's TestClient to exercise every endpoint end-to-end
including request validation, error handling, and response schemas.
"""

import pytest
from fastapi.testclient import TestClient

from backend.services.forecasting.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ── Shared payloads ───────────────────────────────────────────────────

FULL_PAYLOAD = {
    "security_id": "BIAT",
    "date": "2026-02-08",
    "ohlcv": {"open": 100, "high": 102, "low": 99, "close": 101, "volume": 5000},
    "order_book": {"spread": 0.5, "depth": 12000, "imbalance": 0.1},
    "sector": "banking",
    "news": ["Q4 results positive"],
    "indicators": {"rsi": 55},
    "horizon": 3,
    "history": [98 + i * 0.1 for i in range(40)],
}

MINIMAL_PAYLOAD = {
    "security_id": "X",
    "date": "2026-01-01",
    "ohlcv": {"open": 50, "high": 51, "low": 49, "close": 50, "volume": 1000},
}

AUGMENT_PAYLOAD = {
    "security_id": "SOTUMAG",
    "price_history": [45.0 + i * 0.2 for i in range(60)],
    "n_synthetic": 5,
    "method": "vae",
}

TRANSFER_PAYLOAD = {
    "target_security_id": "SOTUMAG",
    "target_prices": [45.0 + i * 0.1 for i in range(60)],
    "source_corpus": {
        "BIAT": [100.0 + i * 0.5 for i in range(60)],
        "BH": [20.0 + i * 0.2 for i in range(60)],
    },
}


# ── POST /api/forecasting/forecast ───────────────────────────────────

class TestForecastEndpoint:
    def test_forecast_full_payload(self, client):
        resp = client.post("/api/forecasting/forecast", json=FULL_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["quantiles"]) == 3
        assert data["horizon_days"] == 3
        assert 0 <= data["liquidity_high_prob"] <= 1
        assert 0 <= data["price_up_prob"] <= 1

    def test_forecast_minimal_payload(self, client):
        resp = client.post("/api/forecasting/forecast", json=MINIMAL_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["quantiles"]) == 1
        assert data["horizon_days"] == 1

    def test_forecast_quantile_ordering(self, client):
        resp = client.post("/api/forecasting/forecast", json=FULL_PAYLOAD)
        data = resp.json()
        for q in data["quantiles"]:
            assert q["p10"] <= q["p50"] <= q["p90"]

    def test_forecast_horizon_5(self, client):
        payload = {**FULL_PAYLOAD, "horizon": 5}
        resp = client.post("/api/forecasting/forecast", json=payload)
        assert resp.status_code == 200
        assert len(resp.json()["quantiles"]) == 5

    def test_forecast_invalid_horizon_0(self, client):
        payload = {**FULL_PAYLOAD, "horizon": 0}
        resp = client.post("/api/forecasting/forecast", json=payload)
        assert resp.status_code == 422  # pydantic validation (ge=1)

    def test_forecast_invalid_horizon_6(self, client):
        payload = {**FULL_PAYLOAD, "horizon": 6}
        resp = client.post("/api/forecasting/forecast", json=payload)
        assert resp.status_code == 422  # pydantic validation (le=5)

    def test_forecast_missing_ohlcv(self, client):
        payload = {"security_id": "X", "date": "2026-01-01"}
        resp = client.post("/api/forecasting/forecast", json=payload)
        assert resp.status_code == 422

    def test_forecast_missing_security_id(self, client):
        payload = {"date": "2026-01-01", "ohlcv": {"open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100}}
        resp = client.post("/api/forecasting/forecast", json=payload)
        assert resp.status_code == 422

    def test_forecast_empty_body(self, client):
        resp = client.post("/api/forecasting/forecast", json={})
        assert resp.status_code == 422


# ── POST /api/forecasting/explain ────────────────────────────────────

class TestExplainEndpoint:
    def test_explain_full_payload(self, client):
        resp = client.post("/api/forecasting/explain", json=FULL_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["confidence_interval"]) == 2
        assert data["confidence_interval"][0] < data["confidence_interval"][1]
        assert len(data["shap_values"]) > 0
        assert len(data["top_drivers"]) > 0

    def test_explain_minimal_payload(self, client):
        resp = client.post("/api/forecasting/explain", json=MINIMAL_PAYLOAD)
        assert resp.status_code == 200

    def test_explain_driver_structure(self, client):
        resp = client.post("/api/forecasting/explain", json=FULL_PAYLOAD)
        data = resp.json()
        for d in data["top_drivers"]:
            assert "feature" in d
            assert "label" in d
            assert "shap_value" in d
            assert d["direction"] in ("positive", "negative")

    def test_explain_shap_has_ohlcv_keys(self, client):
        resp = client.post("/api/forecasting/explain", json=FULL_PAYLOAD)
        data = resp.json()
        for key in ["close", "open", "volume"]:
            assert key in data["shap_values"]


# ── POST /api/forecasting/recommend ──────────────────────────────────

class TestRecommendEndpoint:
    def test_recommend_full_payload(self, client):
        resp = client.post("/api/forecasting/recommend", json=FULL_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["signal"] in {"enter", "exit", "hold", "defer"}
        assert 0 <= data["confidence"] <= 1
        assert len(data["reason"]) > 0
        assert "timing" in data

    def test_recommend_minimal_payload(self, client):
        resp = client.post("/api/forecasting/recommend", json=MINIMAL_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["signal"] in {"enter", "exit", "hold", "defer"}

    def test_recommend_details_keys(self, client):
        resp = client.post("/api/forecasting/recommend", json=FULL_PAYLOAD)
        data = resp.json()
        assert "upside_pct" in data["details"]
        assert "spread_frac_pct" in data["details"]
        assert "liq_high_prob" in data["details"]


# ── POST /api/forecasting/augment ────────────────────────────────────

class TestAugmentEndpoint:
    def test_augment_success(self, client):
        resp = client.post("/api/forecasting/augment", json=AUGMENT_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["n_generated"] == 5
        assert data["method"] == "vae"
        assert len(data["sample_series"]) <= 3

    def test_augment_gan_method(self, client):
        payload = {**AUGMENT_PAYLOAD, "method": "gan"}
        resp = client.post("/api/forecasting/augment", json=payload)
        assert resp.status_code == 200
        assert resp.json()["method"] == "gan"

    def test_augment_custom_count(self, client):
        payload = {**AUGMENT_PAYLOAD, "n_synthetic": 10}
        resp = client.post("/api/forecasting/augment", json=payload)
        assert resp.status_code == 200
        assert resp.json()["n_generated"] == 10

    def test_augment_series_are_lists(self, client):
        resp = client.post("/api/forecasting/augment", json=AUGMENT_PAYLOAD)
        data = resp.json()
        for s in data["sample_series"]:
            assert isinstance(s, list)
            assert all(isinstance(v, (int, float)) for v in s)

    def test_augment_missing_price_history(self, client):
        payload = {"security_id": "X", "n_synthetic": 5}
        resp = client.post("/api/forecasting/augment", json=payload)
        assert resp.status_code == 422

    def test_augment_n_synthetic_too_high(self, client):
        payload = {**AUGMENT_PAYLOAD, "n_synthetic": 100}
        resp = client.post("/api/forecasting/augment", json=payload)
        assert resp.status_code == 422  # le=50

    def test_augment_n_synthetic_zero(self, client):
        payload = {**AUGMENT_PAYLOAD, "n_synthetic": 0}
        resp = client.post("/api/forecasting/augment", json=payload)
        assert resp.status_code == 422  # ge=1


# ── POST /api/forecasting/transfer-learn ─────────────────────────────

class TestTransferLearnEndpoint:
    def test_transfer_learn_success(self, client):
        resp = client.post("/api/forecasting/transfer-learn", json=TRANSFER_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["pretrained"] is True
        assert data["finetuned"] is True
        assert data["pretrain_sources"] == 2
        assert "pinball_loss_q50" in data["metrics"]

    def test_transfer_learn_frozen_layers(self, client):
        resp = client.post("/api/forecasting/transfer-learn", json=TRANSFER_PAYLOAD)
        data = resp.json()
        assert data["frozen_layers"] == 2

    def test_transfer_learn_missing_corpus(self, client):
        payload = {
            "target_security_id": "X",
            "target_prices": [100 + i for i in range(60)],
        }
        resp = client.post("/api/forecasting/transfer-learn", json=payload)
        assert resp.status_code == 422

    def test_transfer_learn_missing_target(self, client):
        payload = {
            "target_security_id": "X",
            "source_corpus": {"A": [100 + i for i in range(60)]},
        }
        resp = client.post("/api/forecasting/transfer-learn", json=payload)
        assert resp.status_code == 422


# ── Schema validation edge cases ─────────────────────────────────────

class TestSchemaValidation:
    def test_wrong_content_type(self, client):
        resp = client.post(
            "/api/forecasting/forecast",
            content="not json",
            headers={"Content-Type": "text/plain"},
        )
        assert resp.status_code == 422

    def test_get_method_not_allowed(self, client):
        resp = client.get("/api/forecasting/forecast")
        assert resp.status_code == 405

    def test_nonexistent_route(self, client):
        resp = client.post("/api/forecasting/nonexistent", json={})
        assert resp.status_code in (404, 405)
