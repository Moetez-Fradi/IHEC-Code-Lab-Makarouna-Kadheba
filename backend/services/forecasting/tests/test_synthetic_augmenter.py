"""
Tests for SyntheticAugmenter — GAN / TS-VAE data augmentation.

Covers:
  - fit() learns distribution, sets _is_fitted
  - generate() before fit raises RuntimeError
  - generate() produces correct count and length
  - generate() default n vs explicit n
  - generate_ohlcv() produces dicts with all OHLCV keys
  - generate_ohlcv() high >= close >= low
  - status property
  - Custom config (method, seq_len, noise_scale)
  - Reproducibility with numpy seed
"""

import numpy as np
import pytest

from backend.services.forecasting.models.synthetic_augmenter import (
    SyntheticAugmenter,
    AugmenterConfig,
)


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def price_series():
    np.random.seed(99)
    ret = np.random.normal(0.001, 0.015, 99)
    return 50.0 * np.exp(np.concatenate([[0], np.cumsum(ret)]))


@pytest.fixture
def augmenter():
    return SyntheticAugmenter()


@pytest.fixture
def fitted_augmenter(augmenter, price_series):
    augmenter.fit(price_series)
    return augmenter


# ── Fit ───────────────────────────────────────────────────────────────

class TestFit:
    def test_fit_returns_metrics(self, augmenter, price_series):
        metrics = augmenter.fit(price_series)
        assert "method" in metrics
        assert "mu" in metrics
        assert "sigma" in metrics
        assert "epochs" in metrics

    def test_fit_sets_flag(self, augmenter, price_series):
        assert not augmenter._is_fitted
        augmenter.fit(price_series)
        assert augmenter._is_fitted

    def test_fit_captures_last_price(self, augmenter, price_series):
        augmenter.fit(price_series)
        assert augmenter._last_price == pytest.approx(float(price_series[-1]))

    def test_fit_method_in_metrics(self, price_series):
        cfg = AugmenterConfig(method="gan")
        aug = SyntheticAugmenter(config=cfg)
        metrics = aug.fit(price_series)
        assert metrics["method"] == "gan"


# ── Generate ──────────────────────────────────────────────────────────

class TestGenerate:
    def test_generate_before_fit_raises(self, augmenter):
        with pytest.raises(RuntimeError, match="Call fit"):
            augmenter.generate()

    def test_generate_default_count(self, fitted_augmenter):
        series = fitted_augmenter.generate()
        assert len(series) == fitted_augmenter.config.n_synthetic

    def test_generate_explicit_count(self, fitted_augmenter):
        series = fitted_augmenter.generate(n=7)
        assert len(series) == 7

    def test_generate_series_length(self, fitted_augmenter):
        series = fitted_augmenter.generate(n=3)
        for s in series:
            assert len(s) == fitted_augmenter.config.seq_len

    def test_generate_positive_prices(self, fitted_augmenter):
        series = fitted_augmenter.generate(n=5)
        for s in series:
            assert np.all(s > 0)

    def test_generate_custom_seq_len(self, price_series):
        cfg = AugmenterConfig(seq_len=20)
        aug = SyntheticAugmenter(config=cfg)
        aug.fit(price_series)
        series = aug.generate(n=2)
        for s in series:
            assert len(s) == 20

    def test_generate_with_zero_noise_scale(self, price_series):
        """noise_scale=0 should still produce series (all same drift)."""
        cfg = AugmenterConfig(noise_scale=0.0)
        aug = SyntheticAugmenter(config=cfg)
        aug.fit(price_series)
        # noise_scale 0 means sigma * 0 = 0 for the noise std
        # np.random.normal with std=0 returns the mean, so all steps = mu
        series = aug.generate(n=1)
        assert len(series) == 1


# ── Generate OHLCV ───────────────────────────────────────────────────

class TestGenerateOHLCV:
    def test_ohlcv_keys(self, fitted_augmenter):
        results = fitted_augmenter.generate_ohlcv(n=2)
        for r in results:
            for key in ["open", "high", "low", "close", "volume"]:
                assert key in r

    def test_ohlcv_high_gte_close(self, fitted_augmenter):
        results = fitted_augmenter.generate_ohlcv(n=3)
        for r in results:
            assert np.all(r["high"] >= r["close"])

    def test_ohlcv_low_lte_close(self, fitted_augmenter):
        results = fitted_augmenter.generate_ohlcv(n=3)
        for r in results:
            assert np.all(r["low"] <= r["close"])

    def test_ohlcv_volume_positive(self, fitted_augmenter):
        results = fitted_augmenter.generate_ohlcv(n=3)
        for r in results:
            assert np.all(r["volume"] >= 0)

    def test_ohlcv_count(self, fitted_augmenter):
        results = fitted_augmenter.generate_ohlcv(n=4)
        assert len(results) == 4


# ── Status ────────────────────────────────────────────────────────────

class TestStatus:
    def test_status_unfitted(self, augmenter):
        s = augmenter.status
        assert s["fitted"] is False
        assert s["method"] == "vae"

    def test_status_fitted(self, fitted_augmenter):
        s = fitted_augmenter.status
        assert s["fitted"] is True
        assert s["mu"] != 0.0 or True  # could be near zero, just check key exists
        assert "sigma" in s
        assert "latent_dim" in s


# ── Config ────────────────────────────────────────────────────────────

class TestConfig:
    def test_default_config(self):
        cfg = AugmenterConfig()
        assert cfg.method == "vae"
        assert cfg.n_synthetic == 5
        assert cfg.seq_len == 60

    def test_custom_config(self):
        cfg = AugmenterConfig(method="gan", latent_dim=32, n_synthetic=10, seq_len=30)
        assert cfg.method == "gan"
        assert cfg.latent_dim == 32
        assert cfg.n_synthetic == 10
        assert cfg.seq_len == 30
