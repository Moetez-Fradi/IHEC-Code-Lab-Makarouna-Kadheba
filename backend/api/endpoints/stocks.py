"""
Stock API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from core.database import get_db
from core.models import Stock, HistoricalPrice
from api.schemas import StockResponse, HistoricalPriceResponse

router = APIRouter()


@router.get("/stocks", response_model=List[StockResponse])
async def get_stocks(
    sector: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get list of all stocks in the BVMT.
    
    Args:
        sector: Filter by sector (optional)
        limit: Maximum number of stocks to return
        db: Database session
        
    Returns:
        List of stocks
    """
    query = db.query(Stock)
    
    if sector:
        query = query.filter(Stock.sector == sector)
    
    stocks = query.limit(limit).all()
    return stocks


@router.get("/stocks/{ticker}", response_model=StockResponse)
async def get_stock(ticker: str, db: Session = Depends(get_db)):
    """
    Get details for a specific stock by ticker.
    
    Args:
        ticker: Stock ticker symbol
        db: Database session
        
    Returns:
        Stock details
        
    Raises:
        HTTPException: If stock not found
    """
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    
    return stock


@router.get("/stocks/{ticker}/history", response_model=List[HistoricalPriceResponse])
async def get_stock_history(
    ticker: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get historical price data for a stock.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date for historical data (optional)
        end_date: End date for historical data (optional)
        limit: Maximum number of records
        db: Database session
        
    Returns:
        List of historical prices
        
    Raises:
        HTTPException: If stock not found
    """
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    
    query = db.query(HistoricalPrice).filter(HistoricalPrice.stock_id == stock.id)
    
    if start_date:
        query = query.filter(HistoricalPrice.date >= start_date)
    if end_date:
        query = query.filter(HistoricalPrice.date <= end_date)
    
    prices = query.order_by(HistoricalPrice.date.desc()).limit(limit).all()
    
    return prices


@router.get("/sectors")
async def get_sectors(db: Session = Depends(get_db)):
    """
    Get list of all sectors in the BVMT.
    
    Returns:
        List of unique sectors
    """
    sectors = db.query(Stock.sector).distinct().all()
    return{"sectors": [s[0] for s in sectors if s[0]]}
