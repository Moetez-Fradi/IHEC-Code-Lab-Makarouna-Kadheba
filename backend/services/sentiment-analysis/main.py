"""
BVMT Sentiment Analysis Service - Main Entry Point
CPU-Optimized Sentiment Analysis for Tunisian Stock Market
"""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.api.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )