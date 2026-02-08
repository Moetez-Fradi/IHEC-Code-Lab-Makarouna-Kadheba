"""
Tests for ForecastExplainer — SHAP values, confidence intervals, top drivers.

Covers:
  - compute_shap() with predict_fn (ablation SHAP)
  - compute_shap() without predict_fn (heuristic fallback)
  - compute_shap() with custom baseline
  - confidence_interval() at default 80 %
  - confidence_interval() at 90 %, 95 %, 50 %
  - confidence_interval() width grows with confidence level
  - top_drivers() ranking by |SHAP|
  - top_drivers() top_k limiting
  - top_drivers() direction labels
  - top_drivers() uses human-readable labels from _FEATURE_LABELS
"""

import pytest

from backend.services.forecasting.explainers import ForecastExplainer, _FEATURE_LABELS


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def features():
    return {
        "close": 101.0,
        "open": 100.0,
        "high": 102.0,
        "low": 99.0,
        "volume": 5000.0,
        "spread": 0.5,
        "depth": 12000.0,
        "rsi": 55.0,
    }


@pytest.fixture
def explainer():
    return ForecastExplainer()


@pytest.fixture
def explainer_with_baseline():
    return ForecastExplainer(baseline={
        "close": 100.0, "open": 100.0, "high": 100.0, "low": 100.0,
        "volume": 3000.0, "spread": 0.4, "depth": 8000.0, "rsi": 50.0,
    })


def _simple_predict(features: dict) -> float:
    """Trivial predict function: sum of all values."""
    return sum(features.values())


# ── compute_shap ──────────────────────────────────────────────────────

class TestComputeShap:
    def test_shap_with_predict_fn(self, explainer, features):
        shap = explainer.compute_shap(features, predict_fn=_simple_predict)
        # Every feature should have a SHAP value
        assert set(shap.keys()) == set(features.keys())

    def test_shap_ablation_correctness(self, explainer, features):
        """Ablating a feature to 0 in a sum-based model should give SHAP = feature_value."""
        shap = explainer.compute_shap(features, predict_fn=_simple_predict)
        for key in features:
            baseline_val = explainer.baseline.get(key, 0.0)
            expected = features[key] - baseline_val  # sum(full) - sum(ablated)
            assert shap[key] == pytest.approx(expected, rel=1e-4)

    def test_shap_without_predict_fn(self, explainer, features):
        shap = explainer.compute_shap(features)
        assert len(shap) == len(features)
        # All values should be floats
        for v in shap.values():
            assert isinstance(v, float)

    def test_shap_heuristic_with_baseline(self, explainer_with_baseline, features):
        shap = explainer_with_baseline.compute_shap(features)
        assert len(shap) == len(features)
        # Volume weight is 0.30 → shap["volume"] = 0.30 * (5000 - 3000) = 600
        assert shap["volume"] == pytest.approx(0.30 * (5000 - 3000), rel=1e-4)

    def test_shap_heuristic_zero_baseline(self, explainer, features):
        """Default baseline is empty → baseline values default to 0."""
        shap = explainer.compute_shap(features)
        # close weight=0.20, baseline=0 → shap = 0.20 * 101.0
        assert shap["close"] == pytest.approx(0.20 * 101.0, rel=1e-4)

    def test_shap_empty_features(self, explainer):
        shap = explainer.compute_shap({})
        assert shap == {}

    def test_shap_unknown_feature_gets_default_weight(self, explainer):
        shap = explainer.compute_shap({"exotic_feature": 42.0})
        # Default weight = 0.01, baseline = 0.0
        assert shap["exotic_feature"] == pytest.approx(0.01 * 42.0, rel=1e-4)


# ── confidence_interval ──────────────────────────────────────────────

class TestConfidenceInterval:
    def test_ci_80_default(self, explainer):
        ci = explainer.confidence_interval(90.0, 110.0)
        assert ci == (90.0, 110.0)

    def test_ci_80_explicit(self, explainer):
        ci = explainer.confidence_interval(90.0, 110.0, confidence=0.80)
        assert ci == (90.0, 110.0)

    def test_ci_90_wider_than_80(self, explainer):
        ci_80 = explainer.confidence_interval(90.0, 110.0, confidence=0.80)
        ci_90 = explainer.confidence_interval(90.0, 110.0, confidence=0.90)
        width_80 = ci_80[1] - ci_80[0]
        width_90 = ci_90[1] - ci_90[0]
        assert width_90 > width_80

    def test_ci_95_wider_than_90(self, explainer):
        ci_90 = explainer.confidence_interval(90.0, 110.0, confidence=0.90)
        ci_95 = explainer.confidence_interval(90.0, 110.0, confidence=0.95)
        width_90 = ci_90[1] - ci_90[0]
        width_95 = ci_95[1] - ci_95[0]
        assert width_95 > width_90

    def test_ci_50_narrower_than_80(self, explainer):
        ci_50 = explainer.confidence_interval(90.0, 110.0, confidence=0.50)
        ci_80 = explainer.confidence_interval(90.0, 110.0, confidence=0.80)
        width_50 = ci_50[1] - ci_50[0]
        width_80 = ci_80[1] - ci_80[0]
        assert width_50 < width_80

    def test_ci_symmetric_around_midpoint(self, explainer):
        ci = explainer.confidence_interval(90.0, 110.0, confidence=0.95)
        mid = (90.0 + 110.0) / 2
        assert ci[0] == pytest.approx(2 * mid - ci[1], rel=1e-4)

    def test_ci_lower_less_than_upper(self, explainer):
        for conf in [0.50, 0.80, 0.90, 0.95, 0.99]:
            ci = explainer.confidence_interval(95.0, 105.0, confidence=conf)
            assert ci[0] < ci[1]


# ── top_drivers ──────────────────────────────────────────────────────

class TestTopDrivers:
    def test_top_drivers_ranking(self, explainer):
        shap = {"a": 10.0, "b": -20.0, "c": 5.0, "d": -1.0}
        drivers = explainer.top_drivers(shap, top_k=4)
        # Ranked by |shap|: b(20), a(10), c(5), d(1)
        assert drivers[0]["feature"] == "b"
        assert drivers[1]["feature"] == "a"
        assert drivers[2]["feature"] == "c"
        assert drivers[3]["feature"] == "d"

    def test_top_drivers_top_k_limiting(self, explainer):
        shap = {"a": 10.0, "b": 20.0, "c": 5.0, "d": 1.0, "e": 15.0}
        drivers = explainer.top_drivers(shap, top_k=3)
        assert len(drivers) == 3

    def test_top_drivers_direction(self, explainer):
        shap = {"x": 5.0, "y": -3.0}
        drivers = explainer.top_drivers(shap, top_k=2)
        x_driver = next(d for d in drivers if d["feature"] == "x")
        y_driver = next(d for d in drivers if d["feature"] == "y")
        assert x_driver["direction"] == "positive"
        assert y_driver["direction"] == "negative"

    def test_top_drivers_labels(self, explainer):
        shap = {"volume": 100.0, "close": 50.0}
        drivers = explainer.top_drivers(shap, top_k=2)
        vol_driver = next(d for d in drivers if d["feature"] == "volume")
        assert vol_driver["label"] == _FEATURE_LABELS["volume"]

    def test_top_drivers_unknown_label_falls_back_to_key(self, explainer):
        shap = {"unknown_feat": 42.0}
        drivers = explainer.top_drivers(shap, top_k=1)
        assert drivers[0]["label"] == "unknown_feat"

    def test_top_drivers_empty_shap(self, explainer):
        drivers = explainer.top_drivers({}, top_k=5)
        assert drivers == []

    def test_top_drivers_has_required_keys(self, explainer):
        shap = {"volume": 10.0}
        drivers = explainer.top_drivers(shap, top_k=1)
        d = drivers[0]
        assert "feature" in d
        assert "label" in d
        assert "shap_value" in d
        assert "direction" in d
