"""Shared type aliases and enums used across the service."""

from enum import Enum


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class RiskProfile(str, Enum):
    """User risk profiles — drives weight adjustment & simulation."""
    CONSERVATEUR = "conservateur"
    MODERE = "modere"
    AGRESSIF = "agressif"


class StressType(str, Enum):
    SECTOR_CRASH = "sector_crash"
    LIQUIDITY_SHOCK = "liquidity_shock"
    INTEREST_RATE_SPIKE = "interest_rate_spike"
    CURRENCY_DEPRECIATION = "currency_depreciation"
    COMPANY_SPECIFIC = "company_specific"
