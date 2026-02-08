"""Forecasting Service — orchestrates all sub-modules.

Coordinates:
  1. QuantileForecaster   — probabilistic price quantiles (p10/p50/p90)
  2. LiquidityModel       — hybrid price-direction + liquidity-regime
  3. TransferLearner      — cross-market pre-train / BVMT fine-tune
  4. SyntheticAugmenter   — GAN / TS-VAE data augmentation
  5. ForecastExplainer    — SHAP + confidence intervals
  6. ExecutionTrigger     — combined enter/exit/hold/defer signal
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from .models.quantile_forecaster import QuantileForecaster, QuantilePrediction
from .models.liquidity_model import LiquidityModel, LiquidityPrediction
from .models.transfer_learner import TransferLearner
from .models.synthetic_augmenter import SyntheticAugmenter, AugmenterConfig
from .explainers import ForecastExplainer
from .execution_trigger import ExecutionTrigger
from .schemas import (
    ForecastOutput,
    ExplainOutput,
    RecommendOutput,
    AugmentOutput,
    TransferLearnOutput,
    QuantileStep,
    DriverDetail,
)


class ForecastingService:
    """Top-level entry point used by the API routes."""

    def __init__(self, data_source=None):
        self.data_source = data_source

        # Sub-modules
        self.quantile_forecaster = QuantileForecaster()
        self.liquidity_model = LiquidityModel()
        self.transfer_learner = TransferLearner()
        self.augmenter = SyntheticAugmenter()
        self.explainer = ForecastExplainer()
        self.trigger = ExecutionTrigger()

    # ------------------------------------------------------------------ #
    # 1. Probabilistic forecast (quantiles + liquidity)
    # ------------------------------------------------------------------ #
    def predict(self, features: Dict[str, Any]) -> ForecastOutput:
        ohlcv = features["ohlcv"]
        order_book = features.get("order_book")
        horizon = features.get("horizon", 1)

        # Build a recent-prices array from history or fall back to close
        history = features.get("history")
        if history and len(history) >= 2:
            recent = np.array(history, dtype=float)
        else:
            recent = np.array([ohlcv["close"]] * 30, dtype=float)

        # Quantile forecast
        q_preds: List[QuantilePrediction] = self.quantile_forecaster.predict(
            recent_prices=recent,
            features=ohlcv,
            horizon=horizon,
        )

        # Liquidity model
        liq: LiquidityPrediction = self.liquidity_model.predict(
            ohlcv=ohlcv,
            order_book=order_book,
        )

        return ForecastOutput(
            quantiles=[
                QuantileStep(
                    horizon_day=qp.horizon_day,
                    p10=qp.p10,
                    p50=qp.p50,
                    p90=qp.p90,
                )
                for qp in q_preds
            ],
            liquidity_high_prob=liq.liquidity_high_prob,
            liquidity_low_prob=liq.liquidity_low_prob,
            price_up_prob=liq.price_up_prob,
            price_down_prob=liq.price_down_prob,
            horizon_days=horizon,
        )

    # ------------------------------------------------------------------ #
    # 2. Explain forecast (SHAP + CI)
    # ------------------------------------------------------------------ #
    def explain_forecast(self, features: Dict[str, Any]) -> ExplainOutput:
        ohlcv = features["ohlcv"]
        order_book = features.get("order_book") or {}
        indicators = features.get("indicators") or {}

        # Merge all numeric features into a single dict for SHAP
        flat_features: Dict[str, float] = {**ohlcv, **order_book, **indicators}

        shap_values = self.explainer.compute_shap(flat_features)

        # Derive quantile CI from a 1-day forecast
        history = features.get("history")
        if history and len(history) >= 2:
            recent = np.array(history, dtype=float)
        else:
            recent = np.array([ohlcv["close"]] * 30, dtype=float)

        q_preds = self.quantile_forecaster.predict(recent, ohlcv, horizon=1)
        ci = self.explainer.confidence_interval(q_preds[0].p10, q_preds[0].p90)

        drivers = self.explainer.top_drivers(shap_values, top_k=5)

        return ExplainOutput(
            confidence_interval=list(ci),
            shap_values=shap_values,
            top_drivers=[DriverDetail(**d) for d in drivers],
        )

    # ------------------------------------------------------------------ #
    # 3. Execution recommendation
    # ------------------------------------------------------------------ #
    def recommend_execution(self, features: Dict[str, Any]) -> RecommendOutput:
        ohlcv = features["ohlcv"]
        order_book = features.get("order_book")

        history = features.get("history")
        if history and len(history) >= 2:
            recent = np.array(history, dtype=float)
        else:
            recent = np.array([ohlcv["close"]] * 30, dtype=float)

        q_preds = self.quantile_forecaster.predict(recent, ohlcv, horizon=1)
        liq = self.liquidity_model.predict(ohlcv=ohlcv, order_book=order_book)

        sig = self.trigger.evaluate(
            quantile_pred=q_preds[0],
            liquidity_pred=liq,
            current_price=ohlcv["close"],
        )

        return RecommendOutput(
            signal=sig.signal,
            confidence=sig.confidence,
            reason=sig.reason,
            timing=sig.timing,
            details=sig.details,
        )

    # ------------------------------------------------------------------ #
    # 4. Synthetic augmentation
    # ------------------------------------------------------------------ #
    def augment(
        self,
        price_history: List[float],
        n_synthetic: int = 5,
        method: str = "vae",
    ) -> AugmentOutput:
        cfg = AugmenterConfig(method=method, n_synthetic=n_synthetic)
        aug = SyntheticAugmenter(config=cfg)
        aug.fit(np.array(price_history, dtype=float))
        series = aug.generate(n_synthetic)

        return AugmentOutput(
            n_generated=len(series),
            method=method,
            sample_series=[s.tolist() for s in series[:3]],
        )

    # ------------------------------------------------------------------ #
    # 5. Transfer learning
    # ------------------------------------------------------------------ #
    def transfer_learn(
        self,
        target_prices: List[float],
        source_corpus: Dict[str, List[float]],
    ) -> TransferLearnOutput:
        corpus_np = {k: np.array(v, dtype=float) for k, v in source_corpus.items()}
        pre_metrics = self.transfer_learner.pre_train(corpus_np)

        ft_metrics = self.transfer_learner.fine_tune(
            np.array(target_prices, dtype=float)
        )

        # Swap in the fine-tuned model as the active forecaster
        self.quantile_forecaster = self.transfer_learner.model

        status = self.transfer_learner.status
        return TransferLearnOutput(
            pretrained=status["pretrained"],
            finetuned=status["finetuned"],
            pretrain_sources=len(source_corpus),
            frozen_layers=status["frozen_layers"],
            metrics={**pre_metrics, **ft_metrics},
        )
