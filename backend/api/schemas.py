"""
Pydantic schemas for API request/response models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Stock Schemas
class StockBase(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    groupe: Optional[str] = None
    code: Optional[str] = None


class StockResponse(StockBase):
    id: int
    
    class Config:
        from_attributes = True


# Historical Price Schemas
class HistoricalPriceResponse(BaseModel):
    date: datetime
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: float
    volume: int
    nb_transactions: int
    capital: float
    
    class Config:
        from_attributes = True


# Prediction Schemas
class PredictionResponse(BaseModel):
    prediction_date: datetime
    target_date: datetime
    predicted_price: float
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    liquidity_class: Optional[str]
    liquidity_probability: Optional[float]
    model_version: Optional[str]
    
    class Config:
        from_attributes = True


# Sentiment Schemas
class SentimentEnum(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class SentimentResponse(BaseModel):
    date: datetime
    score: float
    classification: SentimentEnum
    confidence: Optional[float]
    news_score: Optional[float]
    social_score: Optional[float]
    source_count: int
    
    class Config:
        from_attributes = True


# Anomaly Schemas
class AnomalyTypeEnum(str, Enum):
    VOLUME_SPIKE = "volume_spike"
    PRICE_MANIPULATION = "price_manipulation"
    SENTIMENT_DIVERGENCE = "sentiment_divergence"
    ORDER_SPOOFING = "order_spoofing"
    OTHER = "other"


class SeverityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyResponse(BaseModel):
    id: int
    detected_at: datetime
    anomaly_type: AnomalyTypeEnum
    severity: SeverityEnum
    anomaly_score: float
    description: Optional[str]
    cmf_rule_violated: Optional[str]
    requires_reporting: bool
    investigated: bool
    resolved: bool
    
    class Config:
        from_attributes = True


# Recommendation Schemas
class RecommendationEnum(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class RecommendationResponse(BaseModel):
    recommendation: RecommendationEnum
    confidence: float
    target_price: Optional[float]
    stop_loss: Optional[float]
    explanation: Optional[str]
    risk_level: Optional[str]
    expected_return: Optional[float]
    
    class Config:
        from_attributes = True


# Portfolio Schemas
class PositionResponse(BaseModel):
    stock_id: int
    quantity: float
    avg_buy_price: float
    current_price: Optional[float]
    unrealized_pnl: Optional[float]
    unrealized_pnl_percent: Optional[float]
    
    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    id: int
    name: str
    risk_profile: Optional[str]
    initial_capital: float
    current_value: Optional[float]
    roi: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    positions: List[PositionResponse] = []
    
    class Config:
        from_attributes = True


class PortfolioCreateRequest(BaseModel):
    name: Optional[str] = "My Portfolio"
    risk_profile: str = Field(..., description="conservative, moderate, or aggressive")
    initial_capital: float = Field(..., gt=0)
    user_id: Optional[str] = "demo_user"


# Market Overview Schema
class MarketOverviewResponse(BaseModel):
    tunindex_value: float
    tunindex_change: float
    tunindex_change_percent: float
    total_volume: int
    total_capital: float
    advancing_stocks: int
    declining_stocks: int
    unchanged_stocks: int
    top_gainers: List[dict]
    top_losers: List[dict]
    sentiment_global: float
    recent_anomalies: int
