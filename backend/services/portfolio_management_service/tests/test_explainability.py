"""Tests for explainability: SHAP + LLM interpreter."""

import numpy as np
import pytest

from app.core.config import settings
from app.explainability.interpreter import interpret, _fallback


class TestFallback:
    def test_fallback_output(self):
        shap_result = {
            "top_features": [
                {"name": "weight_0", "impact": 0.15},
                {"name": "price_1", "impact": -0.08},
                {"name": "vol_2", "impact": 0.05},
            ],
            "raw_values": {},
        }
        text = _fallback(shap_result)
        assert "weight_0" in text
        assert "Facteurs" in text

    def test_fallback_with_profile(self):
        shap_result = {
            "top_features": [{"name": "f0", "impact": 0.1}],
            "raw_values": {},
        }
        text = _fallback(shap_result, profile_desc="Profil conservateur")
        assert "conservateur" in text


class TestInterpreter:
    def test_interpret_with_api_key(self):
        """Test LLM interpretation if API key is configured."""
        if not settings.OPENROUTER_API_KEY:
            pytest.skip("No OPENROUTER_API_KEY set")

        shap_result = {
            "top_features": [
                {"name": "gdp_growth", "impact": 0.12},
                {"name": "BIAT_weight", "impact": 0.09},
                {"name": "inflation", "impact": -0.07},
            ],
            "raw_values": {},
        }
        weights = {"BIAT": 0.3, "BH": 0.2, "ATB": 0.5}
        text = interpret(shap_result, weights, profile_desc="Profil modéré")
        assert isinstance(text, str)
        assert len(text) > 20

    def test_interpret_without_key(self):
        """Without API key, falls back to template."""
        original = settings.OPENROUTER_API_KEY
        settings.OPENROUTER_API_KEY = ""
        try:
            shap_result = {
                "top_features": [
                    {"name": "f0", "impact": 0.1},
                    {"name": "f1", "impact": -0.05},
                    {"name": "f2", "impact": 0.03},
                ],
                "raw_values": {},
            }
            text = interpret(shap_result, {"A": 0.5, "B": 0.5})
            assert "Facteurs" in text
        finally:
            settings.OPENROUTER_API_KEY = original
