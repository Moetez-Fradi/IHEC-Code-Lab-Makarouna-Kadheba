"""
Ticker Service
Extract and match stock ticker symbols from text
"""

from typing import Tuple, List, Optional
from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)


class TickerService:
    """Service for extracting ticker information from text."""
    
    @staticmethod
    def extract_ticker_from_text(
        text: str,
        provided_ticker: Optional[str] = None
    ) -> Tuple[Optional[str], List[str]]:
        """
        Extract ticker information from text using keyword matching.
        
        Args:
            text: Input text to analyze
            provided_ticker: Optional ticker provided by user
            
        Returns:
            Tuple of (ticker_symbol, matched_keywords)
        """
        matched_keywords = []
        detected_ticker = None
        
        # Check each ticker's keywords
        for ticker, keywords in settings.TICKER_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    matched_keywords.append(keyword)
                    if detected_ticker is None:
                        detected_ticker = ticker
        
        # Prioritize user-provided ticker if valid
        if provided_ticker and provided_ticker in settings.TICKER_KEYWORDS:
            final_ticker = provided_ticker
        else:
            final_ticker = detected_ticker
        
        if final_ticker:
            logger.info(f"Ticker detected: {final_ticker}, Keywords: {matched_keywords}")
        
        return final_ticker, matched_keywords
    
    @staticmethod
    def get_ticker_info(ticker: str) -> Optional[List[str]]:
        """
        Get keywords associated with a ticker symbol.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            List of keywords or None if ticker not found
        """
        return settings.TICKER_KEYWORDS.get(ticker)


# Initialize service instance
ticker_service = TickerService()