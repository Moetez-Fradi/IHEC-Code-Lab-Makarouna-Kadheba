"""
API Gateway - Main entry point for all API requests
Routes requests to appropriate microservices
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from database import get_db
from models import Stock, HistoricalPrice, Prediction, Sentiment, Anomaly
from config import get_settings

app = FastAPI(
    title="Carthage Alpha API Gateway",
    description="Unified API for all microservices",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "api_version": "1.0.0"}


# ========== STOCK ENDPOINTS ==========
@app.get("/api/stocks")
async def get_stocks(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Stock).offset(skip).limit(limit).all()


@app.get("/api/stocks/{ticker}")
async def get_stock(ticker: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if not stock:
        raise HTTPException(404, detail=f"Stock {ticker} not found")
    return stock


@app.get("/api/stocks/{ticker}/history")
async def get_stock_history(ticker: str, limit: int = 100, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if not stock:
        raise HTTPException(404, detail=f"Stock {ticker} not found")
    return db.query(HistoricalPrice).filter(
        HistoricalPrice.stock_id == stock.id
    ).order_by(desc(HistoricalPrice.date)).limit(limit).all()


# ========== MARKET ENDPOINTS ==========
@app.get("/api/market/overview")
async def get_market_overview(db: Session = Depends(get_db)):
    latest_date = db.query(func.max(HistoricalPrice.date)).scalar()
    if not latest_date:
        return {"tunindex_value": 0, "total_volume": 0}
    
    stats = db.query(
        func.sum(HistoricalPrice.volume).label('volume'),
        func.sum(HistoricalPrice.capital).label('capital')
    ).filter(HistoricalPrice.date == latest_date).first()
    
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
        "tunindex_change_percent": round(sum(c.pct for c in changes) / len(changes), 2) if changes else 0,
        "total_volume": int(stats.volume or 0),
        "total_capital": float(stats.capital or 0),
        "advancing_stocks": sum(1 for c in changes if c.pct > 0),
        "declining_stocks": sum(1 for c in changes if c.pct < 0),
        "top_gainers": [{"ticker": c.ticker, "name": c.name, "change_percent": round(c.pct, 2)} for c in sorted_changes[:5]],
        "top_losers": [{"ticker": c.ticker, "name": c.name, "change_percent": round(c.pct, 2)} for c in sorted_changes[-5:]]
    }


@app.get("/api/market/gainers")
async def get_gainers(limit: int = 10, db: Session = Depends(get_db)):
    latest_date = db.query(func.max(HistoricalPrice.date)).scalar()
    if not latest_date:
        return []
    gainers = db.query(
        Stock.ticker, Stock.name, HistoricalPrice.close,
        ((HistoricalPrice.close - HistoricalPrice.open) / HistoricalPrice.open * 100).label('change')
    ).join(HistoricalPrice).filter(
        HistoricalPrice.date == latest_date, HistoricalPrice.open > 0
    ).order_by(desc('change')).limit(limit).all()
    
    return [
        {"ticker": g.ticker, "name": g.name, "price": g.close, "change_percent": round(g.change, 2)}
        for g in gainers
    ]


@app.get("/api/market/losers")
async def get_losers(limit: int = 10, db: Session = Depends(get_db)):
    latest_date = db.query(func.max(HistoricalPrice.date)).scalar()
    if not latest_date:
        return []
    losers = db.query(
        Stock.ticker, Stock.name, HistoricalPrice.close,
        ((HistoricalPrice.close - HistoricalPrice.open) / HistoricalPrice.open * 100).label('change')
    ).join(HistoricalPrice).filter(
        HistoricalPrice.date == latest_date, HistoricalPrice.open > 0
    ).order_by('change').limit(limit).all()
    
    return [
        {"ticker": l.ticker, "name": l.name, "price": l.close, "change_percent": round(l.change, 2)}
        for l in losers
    ]


@app.get("/api/market/volume")
async def get_volume(db: Session = Depends(get_db)):
    latest_date = db.query(func.max(HistoricalPrice.date)).scalar()
    if not latest_date:
        return {"total_volume": 0}
    stats = db.query(
        func.sum(HistoricalPrice.volume).label('vol'),
        func.sum(HistoricalPrice.capital).label('cap'),
        func.count(HistoricalPrice.id).label('count')
    ).filter(HistoricalPrice.date == latest_date).first()
    return {"total_volume": int(stats.vol or 0), "total_capital": float(stats.cap or 0), "active_stocks": stats.count}


# ========== ML ENDPOINTS (Placeholders) ==========
@app.get("/api/predictions/{ticker}")
async def get_predictions(ticker: str, db: Session = Depends(get_db)):
    return {"ticker": ticker, "predicted_price": 0, "confidence": 0, "status": "placeholder"}


@app.get("/api/sentiment/{ticker}")
async def get_sentiment(ticker: str, db: Session = Depends(get_db)):
    return {"ticker": ticker, "sentiment_score": 0, "label": "neutral", "status": "placeholder"}


@app.get("/api/anomalies")
async def get_anomalies(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Anomaly).order_by(desc(Anomaly.detected_at)).limit(limit).all()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
