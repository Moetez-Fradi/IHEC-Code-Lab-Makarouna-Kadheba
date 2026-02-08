"""
Tests for ExecutionTrigger — combined price + liquidity signal engine.

Covers all branches of the decision matrix:
  - enter:  price_up + liq_ok
  - defer:  price_up + liq_low
  - exit:   price_down + liq_ok
  - defer:  price_down + liq_low
  - hold:   no conviction
  - uncertainty override (wide spread overrides enter/exit → hold)
  - timing choices (intraday vs next_open, next_close, wait_1_day)
  - confidence values
  - details dict contents
  - Custom thresholds
"""

import pytest

from backend.services.forecasting.execution_trigger import (
    ExecutionTrigger,
    ExecutionSignal,
)
from backend.services.forecasting.models.quantile_forecaster import QuantilePrediction
from backend.services.forecasting.models.liquidity_model import LiquidityPrediction


# ── Helpers ───────────────────────────────────────────────────────────

def _qpred(p10=98.0, p50=102.0, p90=104.0, day=1):
    return QuantilePrediction(horizon_day=day, p10=p10, p50=p50, p90=p90)


def _lpred(up=0.6, flat=0.1, down=0.3, liq_high=0.8):
    return LiquidityPrediction(
        price_up_prob=up,
        price_flat_prob=flat,
        price_down_prob=down,
        liquidity_high_prob=liq_high,
        liquidity_low_prob=round(1 - liq_high, 4),
    )


@pytest.fixture
def trigger():
    return ExecutionTrigger()


# ── Enter branch ──────────────────────────────────────────────────────

class TestEnterSignal:
    def test_enter_when_up_and_liquid(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=99, p50=103, p90=105),
            _lpred(up=0.70, down=0.20, liq_high=0.80),
            current_price=100.0,
        )
        assert sig.signal == "enter"

    def test_enter_timing_intraday_high_liq(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=99, p50=103, p90=105),
            _lpred(up=0.70, down=0.20, liq_high=0.85),
            current_price=100.0,
        )
        assert sig.timing == "intraday"

    def test_enter_timing_next_open_moderate_liq(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=99, p50=103, p90=105),
            _lpred(up=0.70, down=0.20, liq_high=0.60),
            current_price=100.0,
        )
        assert sig.timing == "next_open"

    def test_enter_confidence(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=99, p50=103, p90=105),
            _lpred(up=0.70, down=0.20, liq_high=0.80),
            current_price=100.0,
        )
        assert sig.confidence == pytest.approx(min(0.70, 0.80), abs=0.01)


# ── Defer branch (up + low liq) ──────────────────────────────────────

class TestDeferUpSignal:
    def test_defer_when_up_but_illiquid(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=99, p50=103, p90=105),
            _lpred(up=0.70, down=0.20, liq_high=0.30),
            current_price=100.0,
        )
        assert sig.signal == "defer"
        assert sig.timing == "wait_1_day"

    def test_defer_up_confidence_halved(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=99, p50=103, p90=105),
            _lpred(up=0.70, down=0.20, liq_high=0.30),
            current_price=100.0,
        )
        assert sig.confidence == pytest.approx(0.70 * 0.5, abs=0.01)


# ── Exit branch ───────────────────────────────────────────────────────

class TestExitSignal:
    def test_exit_when_down_and_liquid(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=93, p50=96, p90=99),
            _lpred(up=0.20, down=0.70, liq_high=0.80),
            current_price=100.0,
        )
        assert sig.signal == "exit"

    def test_exit_timing_intraday_tight_spread(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=97, p50=96, p90=99),  # spread 2% < 8%
            _lpred(up=0.20, down=0.70, liq_high=0.80),
            current_price=100.0,
        )
        assert sig.timing == "intraday"

    def test_exit_confidence(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=97, p50=96, p90=99),
            _lpred(up=0.20, down=0.70, liq_high=0.80),
            current_price=100.0,
        )
        assert sig.confidence == pytest.approx(min(0.70, 0.80), abs=0.01)


# ── Defer branch (down + low liq) ────────────────────────────────────

class TestDeferDownSignal:
    def test_defer_when_down_but_illiquid(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=93, p50=96, p90=99),
            _lpred(up=0.20, down=0.70, liq_high=0.30),
            current_price=100.0,
        )
        assert sig.signal == "defer"
        assert sig.timing == "wait_1_day"

    def test_defer_down_confidence(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=93, p50=96, p90=99),
            _lpred(up=0.20, down=0.70, liq_high=0.30),
            current_price=100.0,
        )
        assert sig.confidence == pytest.approx(0.70 * 0.4, abs=0.01)


# ── Hold branch ───────────────────────────────────────────────────────

class TestHoldSignal:
    def test_hold_no_conviction(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=99, p50=100, p90=101),
            _lpred(up=0.40, down=0.40, flat=0.20, liq_high=0.80),
            current_price=100.0,
        )
        assert sig.signal == "hold"
        assert sig.timing == "next_open"

    def test_hold_confidence(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=99, p50=100, p90=101),
            _lpred(up=0.40, down=0.40, flat=0.20, liq_high=0.80),
            current_price=100.0,
        )
        expected = 1.0 - max(0.40, 0.40)
        assert sig.confidence == pytest.approx(expected, abs=0.01)


# ── Uncertainty override ─────────────────────────────────────────────

class TestUncertaintyOverride:
    def test_override_enter_to_hold_on_wide_spread(self):
        trigger = ExecutionTrigger(quantile_spread_max=0.03)
        sig = trigger.evaluate(
            _qpred(p10=90, p50=103, p90=110),  # spread 20% >> 3%
            _lpred(up=0.70, down=0.20, liq_high=0.80),
            current_price=100.0,
        )
        assert sig.signal == "hold"
        assert "OVERRIDE" in sig.reason

    def test_override_exit_to_hold_on_wide_spread(self):
        trigger = ExecutionTrigger(quantile_spread_max=0.03)
        sig = trigger.evaluate(
            _qpred(p10=85, p50=95, p90=108),  # spread 23% >> 3%
            _lpred(up=0.20, down=0.70, liq_high=0.80),
            current_price=100.0,
        )
        assert sig.signal == "hold"
        assert "OVERRIDE" in sig.reason
        assert sig.timing == "wait_1_day"


# ── Details dict ──────────────────────────────────────────────────────

class TestDetails:
    def test_details_has_required_keys(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=99, p50=102, p90=104),
            _lpred(up=0.60, down=0.30, liq_high=0.80),
            current_price=100.0,
        )
        assert "upside_pct" in sig.details
        assert "spread_frac_pct" in sig.details
        assert "liq_high_prob" in sig.details
        assert "price_up_prob" in sig.details
        assert "price_down_prob" in sig.details

    def test_details_upside_pct_calculation(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=99, p50=105, p90=110),
            _lpred(up=0.60, down=0.30, liq_high=0.80),
            current_price=100.0,
        )
        assert sig.details["upside_pct"] == pytest.approx(5.0, abs=0.1)

    def test_details_spread_frac_calculation(self, trigger):
        sig = trigger.evaluate(
            _qpred(p10=95, p50=100, p90=105),
            _lpred(up=0.40, down=0.40, liq_high=0.80),
            current_price=100.0,
        )
        assert sig.details["spread_frac_pct"] == pytest.approx(10.0, abs=0.1)


# ── Custom thresholds ────────────────────────────────────────────────

class TestCustomThresholds:
    def test_low_threshold_easier_enter(self):
        trigger = ExecutionTrigger(price_up_threshold=0.30, liquidity_threshold=0.30)
        sig = trigger.evaluate(
            _qpred(p10=99, p50=101, p90=103),
            _lpred(up=0.35, down=0.25, liq_high=0.35),
            current_price=100.0,
        )
        assert sig.signal == "enter"

    def test_high_threshold_forces_hold(self):
        trigger = ExecutionTrigger(price_up_threshold=0.90, price_down_threshold=0.90)
        sig = trigger.evaluate(
            _qpred(p10=99, p50=103, p90=105),
            _lpred(up=0.70, down=0.20, liq_high=0.80),
            current_price=100.0,
        )
        assert sig.signal == "hold"


# ── ExecutionSignal dataclass ─────────────────────────────────────────

class TestExecutionSignal:
    def test_is_dataclass(self, trigger):
        sig = trigger.evaluate(
            _qpred(), _lpred(), current_price=100.0
        )
        assert isinstance(sig, ExecutionSignal)

    def test_signal_values(self, trigger):
        """All possible signals belong to the expected set."""
        sig = trigger.evaluate(
            _qpred(), _lpred(), current_price=100.0
        )
        assert sig.signal in {"enter", "exit", "hold", "defer"}
