"""
Execution trigger engine.

Combines the probabilistic price forecast with the liquidity-regime
prediction to produce an actionable signal:

    • **enter**  — favourable price + high liquidity → buy/execute now
    • **exit**   — price peaking / falling + adequate liquidity → sell
    • **hold**   — no strong conviction or poor liquidity
    • **defer**  — signal exists but liquidity is too thin → wait

Each signal also carries a *timing* recommendation:
    intraday | next_open | next_close | wait_N_days
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .models.quantile_forecaster import QuantilePrediction
from .models.liquidity_model import LiquidityPrediction


@dataclass
class ExecutionSignal:
    signal: str  # enter | exit | hold | defer
    confidence: float  # 0–1
    reason: str
    timing: str  # intraday | next_open | next_close | wait_N_days
    details: Dict[str, float]  # extra numeric context


class ExecutionTrigger:
    """
    Decision engine that fuses price-forecast and liquidity signals.

    Thresholds are configurable; defaults are conservative.
    """

    def __init__(
        self,
        price_up_threshold: float = 0.55,
        price_down_threshold: float = 0.55,
        liquidity_threshold: float = 0.50,
        quantile_spread_max: float = 0.08,  # max p90-p10 spread as fraction
    ):
        self.price_up_thr = price_up_threshold
        self.price_down_thr = price_down_threshold
        self.liq_thr = liquidity_threshold
        self.spread_max = quantile_spread_max

    # ------------------------------------------------------------------
    def evaluate(
        self,
        quantile_pred: QuantilePrediction,
        liquidity_pred: LiquidityPrediction,
        current_price: float,
    ) -> ExecutionSignal:
        """
        Produce an execution signal from the model outputs.
        """
        # ---- Quantile analysis ----
        spread_frac = (quantile_pred.p90 - quantile_pred.p10) / (current_price + 1e-9)
        upside = (quantile_pred.p50 - current_price) / (current_price + 1e-9)

        # ---- Liquidity gate ----
        liq_ok = liquidity_pred.liquidity_high_prob >= self.liq_thr

        # ---- Direction conviction ----
        price_up = liquidity_pred.price_up_prob >= self.price_up_thr
        price_down = liquidity_pred.price_down_prob >= self.price_down_thr

        # ---- Decision matrix ----
        if price_up and liq_ok:
            signal = "enter"
            confidence = min(liquidity_pred.price_up_prob, liquidity_pred.liquidity_high_prob)
            reason = (
                f"Median forecast +{upside*100:.1f}% with "
                f"{liquidity_pred.liquidity_high_prob*100:.0f}% high-liquidity probability"
            )
            timing = "intraday" if liquidity_pred.liquidity_high_prob > 0.7 else "next_open"

        elif price_up and not liq_ok:
            signal = "defer"
            confidence = liquidity_pred.price_up_prob * 0.5
            reason = (
                f"Positive outlook (+{upside*100:.1f}%) but liquidity only "
                f"{liquidity_pred.liquidity_high_prob*100:.0f}% — defer execution"
            )
            timing = "wait_1_day"

        elif price_down and liq_ok:
            signal = "exit"
            confidence = min(liquidity_pred.price_down_prob, liquidity_pred.liquidity_high_prob)
            reason = (
                f"Median forecast {upside*100:.1f}% with adequate liquidity — "
                f"consider exiting"
            )
            timing = "intraday" if spread_frac < self.spread_max else "next_close"

        elif price_down and not liq_ok:
            signal = "defer"
            confidence = liquidity_pred.price_down_prob * 0.4
            reason = "Negative outlook but poor liquidity — defer to avoid slippage"
            timing = "wait_1_day"

        else:
            signal = "hold"
            confidence = 1.0 - max(liquidity_pred.price_up_prob, liquidity_pred.price_down_prob)
            reason = "No strong directional conviction"
            timing = "next_open"

        # ---- Uncertainty override ----
        if spread_frac > self.spread_max and signal in ("enter", "exit"):
            signal = "hold"
            reason += f" [OVERRIDE: quantile spread {spread_frac*100:.1f}% exceeds threshold]"
            timing = "wait_1_day"

        return ExecutionSignal(
            signal=signal,
            confidence=round(confidence, 4),
            reason=reason,
            timing=timing,
            details={
                "upside_pct": round(upside * 100, 2),
                "spread_frac_pct": round(spread_frac * 100, 2),
                "liq_high_prob": liquidity_pred.liquidity_high_prob,
                "price_up_prob": liquidity_pred.price_up_prob,
                "price_down_prob": liquidity_pred.price_down_prob,
            },
        )
