"""Load OHLCV CSV files and merge into a multi‑ticker DataFrame."""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_REQUIRED = {"Date", "Open", "High", "Low", "Close", "Volume"}


def _load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date"])
    if _REQUIRED - set(df.columns):
        raise ValueError(f"{path} missing columns: {_REQUIRED - set(df.columns)}")
    df.set_index("Date", inplace=True)
    df.sort_index(inplace=True)
    return df


def _prefix(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    return df.rename(columns={c: f"{ticker}_{c.lower()}" for c in df.columns})


def load_all(data_dir: str | Path, tickers: list[str]) -> pd.DataFrame:
    """Load per‑ticker CSVs and return one merged DataFrame."""
    frames = []
    for t in tickers:
        p = Path(data_dir) / f"{t}.csv"
        if p.exists():
            frames.append(_prefix(_load_csv(p), t))
            logger.info("Loaded %s – %d rows", t, len(frames[-1]))
        else:
            logger.warning("No CSV for %s", t)
    if not frames:
        return pd.DataFrame()
    merged = frames[0]
    for f in frames[1:]:
        merged = merged.join(f, how="inner")
    return merged


def _random_walk(ticker: str, days: int = 252) -> pd.DataFrame:
    rng = np.random.default_rng(abs(hash(ticker)) % 2**31)
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=days)
    n = len(dates)
    dt = 1 / 252
    lr = rng.normal(0.05 * dt, 0.18 * np.sqrt(dt), n)
    c = 100.0 * np.exp(np.cumsum(lr))
    df = pd.DataFrame({
        "Open": c * (1 + rng.uniform(-0.005, 0.005, n)),
        "High": c * (1 + rng.uniform(0.005, 0.02, n)),
        "Low":  c * (1 - rng.uniform(0.005, 0.02, n)),
        "Close": c,
        "Volume": rng.integers(50_000, 500_000, n),
    }, index=pd.Index(dates, name="Date"))
    return _prefix(df, ticker)


def generate_placeholder(tickers: list[str], days: int = 252) -> pd.DataFrame:
    """Create random‑walk data for every ticker (dev only)."""
    frames = [_random_walk(t, days) for t in tickers]
    merged = frames[0]
    for f in frames[1:]:
        merged = merged.join(f, how="inner")
    return merged
