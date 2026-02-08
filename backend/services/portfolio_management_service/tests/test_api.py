"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestHealth:
    def test_health(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestMacro:
    def test_macro_returns_data(self):
        resp = client.get("/api/v1/macro")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, dict)
        assert "gdp_growth" in data or "policy_rate" in data


class TestPortfolioEndpoint:
    def test_portfolio_initial(self):
        resp = client.get("/api/v1/portfolio")
        assert resp.status_code == 200
        data = resp.json()
        assert "cash" in data
        assert "value" in data
        assert data["value"] > 0


class TestTrain:
    def test_quick_train(self):
        resp = client.post("/api/v1/train", json={
            "timesteps": 1024, "adversarial": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "mean_reward" in data
        assert "mean_value" in data


class TestRecommend:
    def test_recommend_default_profile(self):
        client.post("/api/v1/train", json={"timesteps": 1024})
        resp = client.post("/api/v1/recommend", json={"profile": "modere"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["profile"] == "modere"
        assert "weights" in data
        assert "explanation" in data

    def test_recommend_conservateur(self):
        resp = client.post("/api/v1/recommend", json={"profile": "conservateur"})
        assert resp.status_code == 200
        weights = resp.json()["weights"]
        assert all(w <= 0.16 for w in weights.values())  # max 15 % cap

    def test_recommend_invalid_profile(self):
        resp = client.post("/api/v1/recommend", json={"profile": "yolo"})
        assert resp.status_code == 400


class TestSimulate:
    def test_simulate_default(self):
        client.post("/api/v1/train", json={"timesteps": 1024})
        resp = client.post("/api/v1/simulate", json={"profile": "modere"})
        assert resp.status_code == 200
        data = resp.json()
        assert "roi" in data
        assert "sharpe" in data
        assert "max_drawdown" in data
        assert "daily_values" in data
        assert len(data["daily_values"]) > 1

    def test_simulate_with_capital(self):
        resp = client.post("/api/v1/simulate", json={
            "profile": "agressif", "capital": 50_000,
        })
        assert resp.status_code == 200
        assert resp.json()["initial_capital"] == 50_000


class TestStressTest:
    def test_sector_crash(self):
        client.post("/api/v1/train", json={"timesteps": 1024})
        resp = client.post("/api/v1/stress-test", json={
            "stress_type": "sector_crash", "intensity": 0.15,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "pre_stress" in data
        assert "post_stress" in data
        assert "impact" in data

    def test_invalid_stress_type(self):
        resp = client.post("/api/v1/stress-test", json={
            "stress_type": "nonexistent", "intensity": 0.1,
        })
        assert resp.status_code == 400
