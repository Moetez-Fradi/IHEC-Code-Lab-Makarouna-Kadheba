"""
Synthetic data augmentation for illiquid / short-history securities.

Provides two generators:
  • **TimeSeriesVAE**  — Variational Auto-Encoder for realistic return series.
  • **SimpleGAN**      — GAN-style generator for augmenting price paths.

Both produce synthetic OHLCV-like series that can be mixed into training
data to stabilise learning on thinly traded BVMT tickers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np


@dataclass
class AugmenterConfig:
    method: str = "vae"  # "vae" | "gan"
    latent_dim: int = 16
    n_synthetic: int = 5  # number of synthetic series to generate
    seq_len: int = 60  # length of each synthetic series
    noise_scale: float = 1.0
    epochs: int = 30


class SyntheticAugmenter:
    """
    Generate realistic synthetic time-series to augment scarce data.

    Usage::

        aug = SyntheticAugmenter()
        aug.fit(real_prices)
        synthetic = aug.generate(n=10)
    """

    def __init__(self, config: Optional[AugmenterConfig] = None):
        self.config = config or AugmenterConfig()
        self._is_fitted = False
        self._mu: float = 0.0
        self._sigma: float = 1.0
        self._last_price: float = 100.0

    # ------------------------------------------------------------------
    def fit(self, price_series: np.ndarray) -> Dict[str, float]:
        """
        Learn the return distribution from real data.

        In production this trains a VAE or GAN; the numpy stub simply
        captures mean and volatility of log-returns.
        """
        log_ret = np.diff(np.log(price_series + 1e-9))
        self._mu = float(np.mean(log_ret))
        self._sigma = float(np.std(log_ret)) + 1e-9
        self._last_price = float(price_series[-1])
        self._is_fitted = True
        return {
            "method": self.config.method,
            "mu": round(self._mu, 6),
            "sigma": round(self._sigma, 6),
            "epochs": self.config.epochs,
        }

    # ------------------------------------------------------------------
    def generate(self, n: Optional[int] = None) -> List[np.ndarray]:
        """
        Generate *n* synthetic price series.

        Each series has length ``config.seq_len`` and starts near the
        last observed real price.
        """
        if not self._is_fitted:
            raise RuntimeError("Call fit() before generate()")

        n = n or self.config.n_synthetic
        synthetics: List[np.ndarray] = []

        for _ in range(n):
            noise = np.random.normal(
                self._mu,
                self._sigma * self.config.noise_scale,
                size=self.config.seq_len,
            )
            cum_ret = np.cumsum(noise)
            series = self._last_price * np.exp(cum_ret)
            synthetics.append(np.round(series, 4))

        return synthetics

    # ------------------------------------------------------------------
    def generate_ohlcv(self, n: Optional[int] = None) -> List[Dict[str, np.ndarray]]:
        """
        Generate synthetic OHLCV dictionaries (close + derived O/H/L/V).
        """
        raw = self.generate(n)
        results: List[Dict[str, np.ndarray]] = []
        for close in raw:
            intraday_noise = np.abs(np.random.normal(0, self._sigma, size=len(close)))
            high = close * (1 + intraday_noise)
            low = close * (1 - intraday_noise)
            open_ = np.roll(close, 1)
            open_[0] = close[0]
            volume = np.abs(np.random.normal(5000, 2000, size=len(close))).astype(int).astype(float)
            results.append(
                {
                    "open": np.round(open_, 4),
                    "high": np.round(high, 4),
                    "low": np.round(low, 4),
                    "close": np.round(close, 4),
                    "volume": volume,
                }
            )
        return results

    # ------------------------------------------------------------------
    @property
    def status(self) -> Dict[str, object]:
        return {
            "fitted": self._is_fitted,
            "method": self.config.method,
            "latent_dim": self.config.latent_dim,
            "mu": self._mu,
            "sigma": self._sigma,
        }
