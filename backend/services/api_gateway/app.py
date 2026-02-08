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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

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


# ========== MICROSERVICE PROXIES ==========
import httpx
from fastapi import Query
from datetime import datetime, timedelta

# Service URLs
SERVICE_URLS = {
    "forecasting": "http://localhost:8002",
    "anomaly": "http://localhost:8004",
    "sentiment": "http://localhost:8005",
    "portfolio": "http://localhost:8007",
}

# ========== FORECASTING SERVICE ==========
@app.get("/api/forecast")
async def proxy_forecast(code: str = Query(...), lookback: int = Query(None)):
    """Proxy to forecasting service"""
    params = {"code": code}
    if lookback:
        params["lookback"] = lookback
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.get(f"{SERVICE_URLS['forecasting']}/forecast", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Forecasting service error: {str(e)}")

# ========== SENTIMENT SERVICE ==========
@app.get("/api/sentiment/sentiments/daily")
async def proxy_all_sentiments():
    """Get all sentiments for today"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{SERVICE_URLS['sentiment']}/sentiments/daily")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Sentiment service error: {str(e)}")

@app.get("/api/sentiment/daily/{ticker}")
async def proxy_sentiment_daily(ticker: str, days: int = Query(30)):
    """Proxy to sentiment service for daily aggregated sentiment"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{SERVICE_URLS['sentiment']}/sentiment/daily/{ticker}",
                params={"days": days}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Sentiment service error: {str(e)}")

@app.get("/api/sentiment/articles")
async def proxy_sentiment_articles(ticker: str = Query(None), limit: int = Query(20)):
    """Proxy to sentiment service for articles"""
    params = {"limit": limit}
    if ticker:
        params["ticker"] = ticker
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{SERVICE_URLS['sentiment']}/articles",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Sentiment service error: {str(e)}")

@app.post("/api/sentiment/scrape")
async def proxy_sentiment_scrape():
    """Trigger sentiment scraping"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(f"{SERVICE_URLS['sentiment']}/trigger-scrape")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Sentiment service error: {str(e)}")

@app.post("/api/sentiment/search-social-media")
async def proxy_social_media_search(ticker: str = Query(...)):
    """Search social media for ticker sentiment"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['sentiment']}/search-social-media",
                params={"ticker": ticker}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Sentiment service error: {str(e)}")

# ========== ANOMALY DETECTION SERVICE ==========
@app.get("/api/anomalies")
async def proxy_anomalies(code: str = Query(...), start: str = Query(...), end: str = Query(...)):
    """Proxy to anomaly detection service"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.get(
                f"{SERVICE_URLS['anomaly']}/anomalies",
                params={"code": code, "start": start, "end": end}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Anomaly service error: {str(e)}")

# ========== PORTFOLIO MANAGEMENT SERVICE ==========
@app.post("/api/portfolio/recommend")
async def proxy_portfolio_recommend(request: dict):
    """Proxy to portfolio management service for recommendations"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['portfolio']}/api/v1/recommend",
                json=request
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Portfolio service error: {str(e)}")

@app.post("/api/portfolio/simulate")
async def proxy_portfolio_simulate(request: dict):
    """Proxy to portfolio management service for simulation"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['portfolio']}/api/v1/simulate",
                json=request
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Portfolio service error: {str(e)}")

@app.post("/api/portfolio/stress-test")
async def proxy_portfolio_stress(request: dict):
    """Proxy to portfolio management service for stress testing"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['portfolio']}/api/v1/stress-test",
                json=request
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Portfolio service error: {str(e)}")

@app.get("/api/portfolio/macro")
async def proxy_portfolio_macro():
    """Proxy to portfolio management service for macro data"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{SERVICE_URLS['portfolio']}/api/v1/macro")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Portfolio service error: {str(e)}")

# ========== PREDICTIONS FROM DB ==========
@app.get("/api/predictions/{ticker}")
async def get_predictions(ticker: str, db: Session = Depends(get_db)):
    """Get stored predictions from database"""
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if not stock:
        raise HTTPException(404, detail=f"Stock {ticker} not found")
    
    predictions = db.query(Prediction).filter(
        Prediction.stock_id == stock.id
    ).order_by(Prediction.target_date).all()
    
    return predictions


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
