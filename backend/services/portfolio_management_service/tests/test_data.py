"""Tests for data providers, features, preprocessor."""

import numpy as np
import pandas as pd
import pytest

from app.data import stock_loader, features, preprocessor
from app.data.macro import fetch_macro_snapshot


class TestStockLoader:
    def test_generate_placeholder_shape(self):
        tickers = ["A", "B", "C"]
        df = stock_loader.generate_placeholder(tickers, days=100)
        assert not df.empty
        close_cols = [c for c in df.columns if c.endswith("_close")]
        assert len(close_cols) == 3

    def test_generate_placeholder_columns(self):
        df = stock_loader.generate_placeholder(["X"], days=50)
        expected = {"X_open", "X_high", "X_low", "X_close", "X_volume"}
        assert expected.issubset(set(df.columns))

    def test_load_all_missing_dir(self, tmp_path):
        result = stock_loader.load_all(tmp_path, ["FAKE"])
        assert isinstance(result, pd.DataFrame)
        assert result.empty


class TestFeatures:
    def _make_df(self, n=100):
        return stock_loader.generate_placeholder(["T"], days=n)

    def test_enrich_adds_columns(self):
        df = self._make_df()
        enriched = features.enrich(df)
        assert "T_returns" in enriched.columns
        assert "T_vol" in enriched.columns
        assert "T_rsi" in enriched.columns
        assert not enriched.isnull().any().any()

    def test_add_rsi_bounds(self):
        df = self._make_df(200)
        features.add_rsi(df, col="T_close")
        valid = df["rsi"].dropna()
        assert valid.min() >= 0
        assert valid.max() <= 100


class TestPreprocessor:
    def test_minmax(self):
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = preprocessor.minmax(arr)
        assert pytest.approx(result[0], abs=1e-6) == 0.0
        assert pytest.approx(result[-1], abs=1e-6) == 1.0

    def test_build_state_vector_shape(self):
        n = 4
        macro = {"a": 1.0, "b": 2.0, "c": 3.0}
        vec = preprocessor.build_state_vector(
            np.ones(n) / n, np.ones(n) * 100, np.ones(n) * 0.2,
            macro, 0.0,
        )
        assert vec.shape == (3 * n + len(macro) + 1,)
        assert vec.dtype == np.float32
