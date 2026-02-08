"""
Shared fixtures for the forecasting test suite.

Import any fixture defined here automatically into every test file
under backend/services/forecasting/tests/.
"""

import numpy as np
import pytest


@pytest.fixture
def sample_price_series():
    """60-point synthetic price series (slight uptrend + noise)."""
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 59)
    return 100.0 * np.exp(np.concatenate([[0], np.cumsum(returns)]))


@pytest.fixture
def sample_ohlcv():
    """Standard OHLCV dict for testing."""
    return {
        "open": 100.0,
        "high": 102.0,
        "low": 99.0,
        "close": 101.0,
        "volume": 5000.0,
    }


@pytest.fixture
def sample_order_book():
    """Standard order-book dict for testing."""
    return {
        "spread": 0.5,
        "depth": 12000.0,
        "imbalance": 0.1,
    }


@pytest.fixture
def full_feature_dict(sample_ohlcv, sample_order_book, sample_price_series):
    """Complete feature dict ready for service methods."""
    return {
        "security_id": "BIAT",
        "date": "2026-02-08",
        "ohlcv": sample_ohlcv,
        "order_book": sample_order_book,
        "sector": "banking",
        "news": ["BIAT Q4 results"],
        "indicators": {"rsi": 55.0},
        "horizon": 1,
        "history": sample_price_series.tolist(),
    }
