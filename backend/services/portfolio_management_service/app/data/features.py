"""
Technical‑indicator feature engineering for OHLCV DataFrames.

Every function takes a DataFrame **in‑place** and returns it,
so calls can be chained: ``add_rsi(add_macd(df))``.
"""

import numpy as np
import pandas as pd


def add_returns(df: pd.DataFrame, col: str = "Close") -> pd.DataFrame:
    df["returns"] = df[col].pct_change()
    return df


def add_volatility(df: pd.DataFrame, window: int = 20, col: str = "returns") -> pd.DataFrame:
    df["volatility"] = df[col].rolling(window).std()
    return df


def add_sma(df: pd.DataFrame, window: int = 20, col: str = "Close") -> pd.DataFrame:
    df[f"sma_{window}"] = df[col].rolling(window).mean()
    return df


def add_rsi(df: pd.DataFrame, period: int = 14, col: str = "Close") -> pd.DataFrame:
    delta = df[col].diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / (loss + 1e-10)
    df["rsi"] = 100.0 - 100.0 / (1.0 + rs)
    return df


def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    col: str = "Close",
) -> pd.DataFrame:
    ema_fast = df[col].ewm(span=fast, adjust=False).mean()
    ema_slow = df[col].ewm(span=slow, adjust=False).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    return df


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the full feature pipeline to each ticker's close column."""
    close_cols = [c for c in df.columns if c.endswith("_close")]
    for col in close_cols:
        tag = col.replace("_close", "")
        add_returns(df, col=col)
        df.rename(columns={"returns": f"{tag}_returns"}, inplace=True)
        add_volatility(df, col=f"{tag}_returns")
        df.rename(columns={"volatility": f"{tag}_vol"}, inplace=True)
        add_rsi(df, col=col)
        df.rename(columns={"rsi": f"{tag}_rsi"}, inplace=True)
    df.dropna(inplace=True)
    return df
