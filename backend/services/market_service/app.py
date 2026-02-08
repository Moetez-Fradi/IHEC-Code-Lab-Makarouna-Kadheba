"""
Market Service - FastAPI application for market statistics
"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict, Any
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from database import get_db
from models import Stock, HistoricalPrice

app = FastAPI(
    title="Market Service",
    description="Microservice for market statistics and analytics",
    version="1.0.0"
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "market-service"}


@app.get("/overview")
async def get_market_overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get comprehensive market overview."""
    latest_date = db.query(func.max(HistoricalPrice.date)).scalar()
    
    if not latest_date:
        return {"tunindex_value": 0, "total_volume": 0, "top_gainers": [], "top_losers": []}
    
    # Get statistics
    stats = db.query(
        func.sum(HistoricalPrice.volume).label('volume'),
        func.sum(HistoricalPrice.capital).label('capital')
    ).filter(HistoricalPrice.date == latest_date).first()
    
    # Get price changes
    changes = db.query(
        Stock.ticker, Stock.name, HistoricalPrice.close,
        ((HistoricalPrice.close - HistoricalPrice.open) / HistoricalPrice.open * 100).label('pct')
    ).join(HistoricalPrice).filter(
        HistoricalPrice.date == latest_date, HistoricalPrice.open > 0
    ).all()
    
    sorted_changes = sorted(changes, key=lambda x: x.pct, reverse=True)
    tunindex = sum(c.close for c in changes) / len(changes) if changes else 0
    
    return {
        "tunindex_value": round(tunindex, 2),
        "total_volume": int(stats.volume or 0),
        "total_capital": float(stats.capital or 0),
        "top_gainers": [{"ticker": c.ticker, "name": c.name, "change": round(c.pct, 2)} for c in sorted_changes[:5]],
        "top_losers": [{"ticker": c.ticker, "name": c.name, "change": round(c.pct, 2)} for c in sorted_changes[-5:]]
    }


@app.get("/gainers")
async def get_gainers(limit: int = 10, db: Session = Depends(get_db)):
    """Get top gaining stocks."""
    latest_date = db.query(func.max(HistoricalPrice.date)).scalar()
    if not latest_date:
        return []
    
    gainers = db.query(
        Stock.ticker, Stock.name, HistoricalPrice.close,
        ((HistoricalPrice.close - HistoricalPrice.open) / HistoricalPrice.open * 100).label('change')
    ).join(HistoricalPrice).filter(
        HistoricalPrice.date == latest_date, HistoricalPrice.open > 0
    ).order_by(desc('change')).limit(limit).all()
    
    return [{"ticker": g.ticker, "name": g.name, "price": g.close, "change": round(g.change, 2)} for g in gainers]


@app.get("/losers")
async def get_losers(limit: int = 10, db: Session = Depends(get_db)):
    """Get top losing stocks."""
    latest_date = db.query(func.max(HistoricalPrice.date)).scalar()
    if not latest_date:
        return []
    
    losers = db.query(
        Stock.ticker, Stock.name, HistoricalPrice.close,
        ((HistoricalPrice.close - HistoricalPrice.open) / HistoricalPrice.open * 100).label('change')
    ).join(HistoricalPrice).filter(
        HistoricalPrice.date == latest_date, HistoricalPrice.open > 0
    ).order_by('change').limit(limit).all()
    
    return [{"ticker": l.ticker, "name": l.name, "price": l.close, "change": round(l.change, 2)} for l in losers]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
