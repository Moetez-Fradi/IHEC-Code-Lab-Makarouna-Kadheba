"""Pydantic schemas for the forecasting service API."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# ── Request schemas ───────────────────────────────────────────────────

class FeatureInput(BaseModel):
    security_id: str = Field(..., description="Security identifier")
    date: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    ohlcv: Dict[str, float] = Field(
        ..., description="OHLCV data: open, high, low, close, volume"
    )
    order_book: Optional[Dict[str, float]] = Field(
        None, description="Order book features: spread, depth, imbalance"
    )
    sector: Optional[str] = Field(None, description="Sector or cross-list info")
    news: Optional[List[str]] = Field(
        None, description="Relevant news headlines or events"
    )
    indicators: Optional[Dict[str, float]] = Field(
        None, description="Technical indicators (e.g., RSI, MACD)"
    )
    horizon: int = Field(
        1, ge=1, le=5, description="Forecast horizon in days (1\u20135)"
    )
    history: Optional[List[float]] = Field(
        None,
        description="Recent close-price history (\u226530 points) for model input",
    )


class AugmentRequest(BaseModel):
    security_id: str = Field(..., description="Security identifier")
    price_history: List[float] = Field(
        ..., description="Historical close prices for fitting the generator"
    )
    n_synthetic: int = Field(
        5, ge=1, le=50, description="Number of synthetic series to generate"
    )
    method: str = Field(
        "vae", description="Augmentation method: 'vae' or 'gan'"
    )


class TransferLearnRequest(BaseModel):
    target_security_id: str = Field(
        ..., description="BVMT security to fine-tune on"
    )
    target_prices: List[float] = Field(
        ..., description="Price history of the target security"
    )
    source_corpus: Dict[str, List[float]] = Field(
        ...,
        description="Dict of {security_id: price_history} for pre-training",
    )


# ── Response schemas ──────────────────────────────────────────────────

class QuantileStep(BaseModel):
    horizon_day: int = Field(..., description="Day offset (1 = tomorrow)")
    p10: float = Field(..., description="10th percentile price forecast")
    p50: float = Field(..., description="Median price forecast")
    p90: float = Field(..., description="90th percentile price forecast")


class ForecastOutput(BaseModel):
    quantiles: List[QuantileStep] = Field(
        ..., description="Quantile forecasts per horizon day"
    )
    liquidity_high_prob: float = Field(
        ..., description="Probability of high liquidity (0-1)"
    )
    liquidity_low_prob: float = Field(
        ..., description="Probability of low liquidity (0-1)"
    )
    price_up_prob: float = Field(
        ..., description="Probability of price going up"
    )
    price_down_prob: float = Field(
        ..., description="Probability of price going down"
    )
    horizon_days: int = Field(..., description="Forecast horizon in days")


class DriverDetail(BaseModel):
    feature: str
    label: str
    shap_value: float
    direction: str


class ExplainOutput(BaseModel):
    confidence_interval: List[float] = Field(
        ..., description="[lower, upper] confidence interval for forecast"
    )
    shap_values: Dict[str, float] = Field(
        ..., description="SHAP values for each feature"
    )
    top_drivers: List[DriverDetail] = Field(
        ..., description="Top features driving the forecast"
    )


class RecommendOutput(BaseModel):
    signal: str = Field(
        ..., description="Recommended action: 'enter', 'exit', 'hold', 'defer'"
    )
    confidence: float = Field(..., description="Signal confidence (0-1)")
    reason: str = Field(..., description="Explanation for the recommendation")
    timing: str = Field(
        ...,
        description="Suggested timing: 'intraday', 'next_open', 'next_close', 'wait_N_days'",
    )
    details: Dict[str, float] = Field(
        ..., description="Numeric details behind the signal"
    )


class AugmentOutput(BaseModel):
    n_generated: int = Field(..., description="Number of synthetic series generated")
    method: str = Field(..., description="Method used (vae / gan)")
    sample_series: List[List[float]] = Field(
        ..., description="First few synthetic close-price series for inspection"
    )


class TransferLearnOutput(BaseModel):
    pretrained: bool
    finetuned: bool
    pretrain_sources: int
    frozen_layers: int
    metrics: Dict[str, float]
