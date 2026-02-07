"""
Market overview API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from core.database import get_db
from core.models import Stock, HistoricalPrice, Sentiment, Anomaly
from api.schemas import MarketOverviewResponse

router = APIRouter()


@router.get("/overview", response_model=MarketOverviewResponse)
async def get_market_overview(db: Session = Depends(get_db)):
    """
    Get comprehensive market overview including TUNINDEX and market statistics.
    
    Returns:
        Market overview with TUNINDEX, volume, top movers, sentiment
    """
    # Get latest date
    latest_date = db.query(func.max(HistoricalPrice.date)).scalar()
    
    if not latest_date:
        return MarketOverviewResponse(
            tunindex_value=0,
            tunindex_change=0,
            tunindex_change_percent=0,
            total_volume=0,
            total_capital=0,
            advancing_stocks=0,
            declining_stocks=0,
            unchanged_stocks=0,
            top_gainers=[],
            top_losers=[],
            sentiment_global=0,
            recent_anomalies=0
        )
    
    previous_date = latest_date - timedelta(days=1)
    
    # Calculate total volume and capital for latest date
    latest_stats = db.query(
        func.sum(HistoricalPrice.volume).label('total_volume'),
        func.sum(HistoricalPrice.capital).label('total_capital')
    ).filter(HistoricalPrice.date == latest_date).first()
    
    # Get top gainers and losers
    price_changes = db.query(
        Stock.ticker,
        Stock.name,
        HistoricalPrice.close,
        ((HistoricalPrice.close - HistoricalPrice.open) / HistoricalPrice.open * 100).label('change_percent')
    ).join(HistoricalPrice).filter(
        HistoricalPrice.date == latest_date,
        HistoricalPrice.open > 0
    ).all()
    
    # Count advancing/declining stocks
    advancing = sum(1 for p in price_changes if p.change_percent > 0)
    declining = sum(1 for p in price_changes if p.change_percent < 0)
    unchanged = sum(1 for p in price_changes if p.change_percent == 0)
    
    # Sort for top gainers and losers
    sorted_changes = sorted(price_changes, key=lambda x: x.change_percent, reverse=True)
    top_gainers = [
        {"ticker": p.ticker, "name": p.name, "price": p.close, "change_percent": round(p.change_percent, 2)}
        for p in sorted_changes[:5]
    ]
    top_losers = [
        {"ticker": p.ticker, "name": p.name, "price": p.close, "change_percent": round(p.change_percent, 2)}
        for p in sorted_changes[-5:]
    ]
    
    # Get global sentiment (average of all stocks today)
    avg_sentiment = db.query(func.avg(Sentiment.score)).filter(
        Sentiment.date == latest_date
    ).scalar() or 0
    
    # Count recent anomalies (last 24 hours)
    recent_anomalies = db.query(func.count(Anomaly.id)).filter(
        Anomaly.detected_at >= datetime.utcnow() - timedelta(hours=24)
    ).scalar() or 0
    
    # Calculate TUNINDEX (simplified - weighted average of all stocks)
    # In reality, TUNINDEX has specific calculation methodology
    tunindex_value = sum(p.close for p in price_changes) / len(price_changes) if price_changes else 0
    tunindex_change = sum(p.change_percent for p in price_changes) / len(price_changes) if price_changes else 0
    
    return MarketOverviewResponse(
        tunindex_value=round(tunindex_value, 2),
        tunindex_change=round(tunindex_change, 2),
        tunindex_change_percent=round(tunindex_change, 2),
        total_volume=int(latest_stats.total_volume or 0),
        total_capital=float(latest_stats.total_capital or 0),
        advancing_stocks=advancing,
        declining_stocks=declining,
        unchanged_stocks=unchanged,
        top_gainers=top_gainers,
        top_losers=top_losers,
        sentiment_global=round(float(avg_sentiment), 3),
        recent_anomalies=recent_anomalies
    )
