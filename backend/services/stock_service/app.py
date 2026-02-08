"""
Stock Service - FastAPI application for stock data operations
"""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import sys
import os

# Add parent for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from database import get_db, SessionLocal
from models import Stock, HistoricalPrice

app = FastAPI(
    title="Stock Service",
    description="Microservice for stock data operations",
    version="1.0.0"
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "stock-service"}


@app.get("/stocks")
async def get_all_stocks(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Get all stocks with pagination."""
    return db.query(Stock).offset(skip).limit(limit).all()


@app.get("/stocks/{ticker}")
async def get_stock(ticker: str, db: Session = Depends(get_db)):
    """Get stock by ticker."""
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    return stock


@app.get("/stocks/{ticker}/history")
async def get_stock_history(ticker: str, limit: int = 100, db: Session = Depends(get_db)):
    """Get historical prices for a stock."""
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    
    history = db.query(HistoricalPrice).filter(
        HistoricalPrice.stock_id == stock.id
    ).order_by(desc(HistoricalPrice.date)).limit(limit).all()
    
    return history


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
