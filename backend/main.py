"""
Carthage Alpha - FastAPI Main Application
Intelligent Trading Assistant for BVMT
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys

from core.config import get_settings
from core.database import init_db
from api.endpoints import stocks, predictions, sentiment, anomalies, portfolio, market

# Initialize settings
settings = get_settings()

# Configure logging
logger.remove()
logger.add(sys.stdout, level=settings.log_level)
logger.add(settings.log_file, rotation="500 MB", level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Carthage Alpha API...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    yield
    
    logger.info("Shutting down Carthage Alpha API...")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Carthage Alpha API",
        "version": settings.api_version,
        "description": "Intelligent Trading Assistant for BVMT",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "stocks": "/api/stocks",
            "market": "/api/market",
            "predictions": "/api/predictions",
            "sentiment": "/api/sentiment",
            "anomalies": "/api/anomalies",
            "portfolio": "/api/portfolio"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "api_version": settings.api_version
    }


# Include API routers
app.include_router(stocks.router, prefix="/api", tags=["Stocks"])
app.include_router(market.router, prefix="/api/market", tags=["Market"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["Sentiment"])
app.include_router(anomalies.router, prefix="/api/anomalies", tags=["Anomalies"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch-all exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
