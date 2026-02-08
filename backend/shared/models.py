"""
SQLAlchemy database models for Carthage Alpha.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class Stock(Base):
    """Stock metadata table."""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    sector = Column(String(100))
    groupe = Column(String(10))
    code = Column(String(20), unique=True)
    
    # Relationships
    prices = relationship("HistoricalPrice", back_populates="stock")
    predictions = relationship("Prediction", back_populates="stock")
    sentiments = relationship("Sentiment", back_populates="stock")
    anomalies = relationship("Anomaly", back_populates="stock")


class HistoricalPrice(Base):
    """Historical OHLCV price data (TimescaleDB hypertable)."""
    __tablename__ = "historical_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    
    # OHLCV data
    open =  Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, nullable=False)
    volume = Column(Integer, default=0)
    
    # Additional metrics
    nb_transactions = Column(Integer, default=0)
    capital = Column(Float, default=0)
    
    # Relationships
    stock = relationship("Stock", back_populates="prices")


class Prediction(Base):
    """Price predictions with confidence intervals."""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    prediction_date = Column(DateTime, nullable=False)
    target_date = Column(DateTime, nullable=False)
    
    # Prediction values
    predicted_price = Column(Float, nullable=False)
    lower_bound = Column(Float)  # 90% confidence interval
    upper_bound = Column(Float)
    
    # Liquidity prediction
    liquidity_class = Column(String(20))  # Liquid, Moderately Liquid, Illiquid
    liquidity_probability = Column(Float)
    
    # Metadata
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="predictions")


class SentimentEnum(str, enum.Enum):
    """Sentiment classification."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Sentiment(Base):
    """Sentiment analysis scores."""
    __tablename__ = "sentiments"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    
    # Sentiment scores
    score = Column(Float, nullable=False)  # -1 to +1
    classification = Column(Enum(SentimentEnum))
    confidence = Column(Float)
    
    # Sources
    news_score = Column(Float)
    social_score = Column(Float)
    
    # Metadata
    source_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="sentiments")


class AnomalyTypeEnum(str, enum.Enum):
    """Anomaly type classification."""
    VOLUME_SPIKE = "volume_spike"
    PRICE_MANIPULATION = "price_manipulation"
    SENTIMENT_DIVERGENCE = "sentiment_divergence"
    ORDER_SPOOFING = "order_spoofing"
    OTHER = "other"


class SeverityEnum(str, enum.Enum):
    """Anomaly severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Anomaly(Base):
    """Detected market anomalies."""
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    detected_at = Column(DateTime, nullable=False, index=True)
    
    # Anomaly details
    anomaly_type = Column(Enum(AnomalyTypeEnum), nullable=False)
    severity = Column(Enum(SeverityEnum), default=SeverityEnum.MEDIUM)
    anomaly_score = Column(Float, nullable=False)  # 0 to 1
    
    # Description
    description = Column(Text)
    details = Column(Text)  # JSON string with additional data
    
    # CMF Compliance
    cmf_rule_violated = Column(String(100))
    requires_reporting = Column(Boolean, default=False)
    
    # Status
    investigated = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    
    # Relationships
    stock = relationship("Stock", back_populates="anomalies")


class RecommendationEnum(str, enum.Enum):
    """Investment recommendation types."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class Recommendation(Base):
    """AI-generated investment recommendations."""
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Recommendation
    recommendation = Column(Enum(RecommendationEnum), nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Price targets
    target_price = Column(Float)
    stop_loss = Column(Float)
    
    # Explanation (XAI)
    explanation = Column(Text)
    shap_values = Column(Text)  # JSON string with SHAP attributions
    
    # Risk assessment
    risk_level = Column(String(20))
    expected_return = Column(Float)
    max_drawdown = Column(Float)


class Portfolio(Base):
    """User portfolio simulations."""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)  # Can be linked to auth system later
    name = Column(String(200), default="My Portfolio")
    
    # Configuration
    risk_profile = Column(String(20))  # conservative, moderate, aggressive
    initial_capital = Column(Float, nullable=False)
    current_value = Column(Float)
    
    # Performance metrics
    roi = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    positions = relationship("Position", back_populates="portfolio")


class Position(Base):
    """Individual stock positions in portfolio."""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    
    # Position details
    quantity = Column(Float, nullable=False)
    avg_buy_price = Column(Float, nullable=False)
    current_price = Column(Float)
    
    # Performance
    unrealized_pnl = Column(Float)
    unrealized_pnl_percent = Column(Float)
    
    # Metadata
    opened_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
