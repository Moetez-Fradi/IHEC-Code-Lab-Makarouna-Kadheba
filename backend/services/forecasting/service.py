"""
Forecasting Service – Feature engineering and prediction logic
───────────────────────────────────────────────────────────────
On-the-fly training approach: for each prediction request we
fetch historical data, compute features, train lightweight
XGBoost models, and return 5-day forecasts with confidence
intervals and liquidity probabilities.

Pre-trained models can also be loaded from disk if available.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import mean_squared_error, mean_absolute_error

from config import config
from db import fetch_stock_history

logger = logging.getLogger(__name__)

FORECAST_HORIZON = config.forecast_horizon


# ── Data classes for the response ────────────────────────────────────────────

@dataclass
class DayForecast:
    date: str
    predicted_close: float
    confidence_low: float
    confidence_high: float
    predicted_volume: float
    liquidity_probability: float
    liquidity_label: str  # "high" or "low"


@dataclass
class ForecastReport:
    stock_code: str
    stock_name: str
    forecast_from: str
    horizon: int
    model: str
    daily_forecasts: list[DayForecast]
    metrics: dict
    historical_close: list[dict]  # last N days for chart context


# ── Feature Engineering ──────────────────────────────────────────────────────

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a rich feature set from raw OHLCV data.
    `df` must have columns: CLOTURE, OUVERTURE, PLUS_HAUT, PLUS_BAS,
    QUANTITE_NEGOCIEE, CAPITAUX, NB_TRANSACTION and a datetime index.
    """
    feat = pd.DataFrame(index=df.index)

    feat['close'] = df['CLOTURE']
    feat['open'] = df['OUVERTURE']
    feat['high'] = df['PLUS_HAUT']
    feat['low'] = df['PLUS_BAS']
    feat['volume'] = df['QUANTITE_NEGOCIEE']

    # Returns
    feat['return_1d'] = feat['close'].pct_change()
    feat['return_5d'] = feat['close'].pct_change(5)
    feat['return_10d'] = feat['close'].pct_change(10)

    # Lagged prices
    for lag in [1, 2, 3, 5, 10, 20]:
        feat[f'close_lag_{lag}'] = feat['close'].shift(lag)

    # Moving averages
    for window in [5, 10, 20, 50]:
        feat[f'ma_{window}'] = feat['close'].rolling(window).mean()
        feat[f'ma_ratio_{window}'] = feat['close'] / feat[f'ma_{window}']

    # EMA & MACD
    feat['ema_12'] = feat['close'].ewm(span=12).mean()
    feat['ema_26'] = feat['close'].ewm(span=26).mean()
    feat['macd'] = feat['ema_12'] - feat['ema_26']
    feat['macd_signal'] = feat['macd'].ewm(span=9).mean()
    feat['macd_hist'] = feat['macd'] - feat['macd_signal']

    # Volatility
    feat['volatility_5'] = feat['return_1d'].rolling(5).std()
    feat['volatility_20'] = feat['return_1d'].rolling(20).std()

    # RSI
    feat['rsi_14'] = compute_rsi(feat['close'], 14)

    # Bollinger Bands
    bb_ma = feat['close'].rolling(20).mean()
    bb_std = feat['close'].rolling(20).std()
    feat['bb_upper'] = bb_ma + 2 * bb_std
    feat['bb_lower'] = bb_ma - 2 * bb_std
    feat['bb_width'] = (feat['bb_upper'] - feat['bb_lower']) / bb_ma
    feat['bb_position'] = (feat['close'] - feat['bb_lower']) / (feat['bb_upper'] - feat['bb_lower'])

    # Volume features
    feat['volume_ma_5'] = feat['volume'].rolling(5).mean()
    feat['volume_ma_20'] = feat['volume'].rolling(20).mean()
    feat['volume_ratio'] = feat['volume'] / feat['volume_ma_20']

    # Candlestick
    feat['body'] = feat['close'] - feat['open']
    feat['body_pct'] = feat['body'] / feat['open']
    feat['upper_shadow'] = feat['high'] - feat[['close', 'open']].max(axis=1)
    feat['lower_shadow'] = feat[['close', 'open']].min(axis=1) - feat['low']

    # Calendar
    feat['day_of_week'] = df.index.dayofweek
    feat['month'] = df.index.month

    # Capitaux
    feat['capitaux'] = df['CAPITAUX']
    feat['capitaux_ma_10'] = feat['capitaux'].rolling(10).mean()

    return feat


# ── Training & Prediction ───────────────────────────────────────────────────

def _train_xgb_models(
    X_train: pd.DataFrame,
    y_train: pd.DataFrame,
    X_val: pd.DataFrame,
    y_val: pd.DataFrame,
    n_estimators: int,
    max_depth: int,
    early_stopping: int,
) -> dict[int, xgb.XGBRegressor]:
    """Train one XGBoost model per horizon step."""
    models = {}
    for h in range(1, FORECAST_HORIZON + 1):
        col = f'target_t{h}'
        model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=config.xgb_learning_rate,
            subsample=config.xgb_subsample,
            colsample_bytree=config.xgb_colsample_bytree,
            min_child_weight=5,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            verbosity=0,
            early_stopping_rounds=early_stopping,
        )
        model.fit(
            X_train, y_train[col],
            eval_set=[(X_val, y_val[col])],
            verbose=False,
        )
        models[h] = model
    return models


async def run_forecast(code: str, lookback: int | None = None) -> ForecastReport:
    """
    Full forecasting pipeline for a stock:
    1. Fetch data from DB
    2. Engineer features
    3. Train XGBoost models (on-the-fly)
    4. Predict next 5 business days
    5. Return structured report
    """
    lookback = lookback or config.default_lookback_days

    # ── 1. Fetch data ────────────────────────────────────────
    rows = await fetch_stock_history(code, limit=lookback)
    if len(rows) < config.min_history_days:
        raise ValueError(
            f"Not enough data for {code}: got {len(rows)} rows, "
            f"need at least {config.min_history_days}"
        )

    stock_name = rows[0].get("VALEUR", code)

    # Build DataFrame
    df = pd.DataFrame(rows)
    df['SEANCE'] = pd.to_datetime(df['SEANCE'])
    df = df.set_index('SEANCE').sort_index()

    # Ensure numeric
    for col in ['OUVERTURE', 'CLOTURE', 'PLUS_HAUT', 'PLUS_BAS',
                'QUANTITE_NEGOCIEE', 'CAPITAUX', 'NB_TRANSACTION']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['CLOTURE'])
    df = df[df['CLOTURE'] > 0]

    # ── 2. Feature engineering ───────────────────────────────
    features = engineer_features(df)

    # Create targets
    price_targets = pd.DataFrame(index=features.index)
    volume_targets = pd.DataFrame(index=features.index)
    for h in range(1, FORECAST_HORIZON + 1):
        price_targets[f'target_t{h}'] = features['close'].shift(-h)
        volume_targets[f'target_t{h}'] = features['volume'].shift(-h)

    # Liquidity labels (volume > rolling median)
    rolling_median = features['volume'].rolling(20).median()
    liquidity_labels = (features['volume'] > rolling_median).astype(int)
    liq_targets = pd.DataFrame(index=features.index)
    for h in range(1, FORECAST_HORIZON + 1):
        liq_targets[f'target_t{h}'] = liquidity_labels.shift(-h)

    # Drop NaN (from feature lag + target shift)
    feature_cols = list(features.columns)

    # For training: need rows with all targets filled
    train_mask = price_targets.notna().all(axis=1) & features.notna().all(axis=1)
    train_df = features[train_mask]
    price_train_targets = price_targets[train_mask]
    volume_train_targets = volume_targets[train_mask]
    liq_train_targets = liq_targets[train_mask]

    if len(train_df) < 60:
        raise ValueError(f"Insufficient clean data for training: {len(train_df)} rows")

    # Val split: last 20% or 40 days, whichever is smaller
    val_size = min(40, len(train_df) // 5)
    X_train = train_df.iloc[:-val_size]
    X_val = train_df.iloc[-val_size:]
    y_price_train = price_train_targets.iloc[:-val_size]
    y_price_val = price_train_targets.iloc[-val_size:]
    y_vol_train = volume_train_targets.iloc[:-val_size]
    y_vol_val = volume_train_targets.iloc[-val_size:]

    # ── 3. Train models ──────────────────────────────────────
    logger.info(f"Training price models for {code} ({len(X_train)} train samples)...")
    price_models = _train_xgb_models(
        X_train, y_price_train, X_val, y_price_val,
        config.xgb_n_estimators, config.xgb_max_depth, config.xgb_early_stopping,
    )

    logger.info(f"Training volume models for {code}...")
    volume_models = _train_xgb_models(
        X_train, y_vol_train, X_val, y_vol_val,
        config.vol_n_estimators, config.vol_max_depth, 20,
    )

    # Liquidity classifiers
    liq_models = {}
    liq_X_train = X_train.copy()
    liq_X_val = X_val.copy()
    for h in range(1, FORECAST_HORIZON + 1):
        col = f'target_t{h}'
        y_liq_train = liq_train_targets.iloc[:-val_size][col].dropna()
        common_idx = liq_X_train.index.intersection(y_liq_train.index)
        clf = RandomForestClassifier(
            n_estimators=config.liq_n_estimators,
            max_depth=config.liq_max_depth,
            random_state=42,
            n_jobs=-1,
        )
        clf.fit(liq_X_train.loc[common_idx], y_liq_train.loc[common_idx])
        liq_models[h] = clf

    # ── 4. Predict ───────────────────────────────────────────
    # Use the LAST row of features as "today"
    last_features = features.dropna()
    if len(last_features) == 0:
        raise ValueError("No valid feature rows after dropping NaN")

    today_row = last_features.iloc[[-1]]
    today_date = last_features.index[-1]

    # Generate next 5 business days
    future_dates = pd.bdate_range(
        start=today_date + pd.Timedelta(days=1),
        periods=FORECAST_HORIZON,
    )

    # Compute confidence intervals from validation residuals
    val_residuals = {}
    for h in range(1, FORECAST_HORIZON + 1):
        pred = price_models[h].predict(X_val)
        actual = y_price_val[f'target_t{h}'].values
        val_residuals[h] = np.std(actual - pred)

    daily_forecasts = []
    for h in range(1, FORECAST_HORIZON + 1):
        price_pred = float(price_models[h].predict(today_row)[0])
        vol_pred = float(max(0, volume_models[h].predict(today_row)[0]))
        liq_prob = float(liq_models[h].predict_proba(today_row)[0][1])

        # Confidence grows with horizon
        ci_width = 1.96 * val_residuals[h] * np.sqrt(h)

        daily_forecasts.append(DayForecast(
            date=future_dates[h - 1].strftime('%Y-%m-%d'),
            predicted_close=round(price_pred, 3),
            confidence_low=round(price_pred - ci_width, 3),
            confidence_high=round(price_pred + ci_width, 3),
            predicted_volume=round(vol_pred, 0),
            liquidity_probability=round(liq_prob, 4),
            liquidity_label="high" if liq_prob > 0.5 else "low",
        ))

    # ── 5. Metrics (on validation set) ───────────────────────
    metrics = {}
    for h in range(1, FORECAST_HORIZON + 1):
        pred = price_models[h].predict(X_val)
        actual = y_price_val[f'target_t{h}'].values
        prev = X_val['close'].values

        rmse = float(np.sqrt(mean_squared_error(actual, pred)))
        mae = float(mean_absolute_error(actual, pred))
        mape = float(np.mean(np.abs((actual - pred) / actual)) * 100)

        actual_dir = np.sign(actual - prev)
        pred_dir = np.sign(pred - prev)
        da = float(np.mean(actual_dir == pred_dir) * 100)

        metrics[f't+{h}'] = {
            'rmse': round(rmse, 4),
            'mae': round(mae, 4),
            'mape': round(mape, 2),
            'directional_accuracy': round(da, 2),
        }

    # Historical data for chart context (last 60 days)
    hist_window = min(60, len(df))
    historical = [
        {
            'date': idx.strftime('%Y-%m-%d'),
            'close': round(float(row['CLOTURE']), 3),
            'volume': float(row['QUANTITE_NEGOCIEE']),
        }
        for idx, row in df.iloc[-hist_window:].iterrows()
    ]

    return ForecastReport(
        stock_code=code,
        stock_name=stock_name.strip() if isinstance(stock_name, str) else code,
        forecast_from=today_date.strftime('%Y-%m-%d'),
        horizon=FORECAST_HORIZON,
        model='XGBoost (on-the-fly)',
        daily_forecasts=daily_forecasts,
        metrics=metrics,
        historical_close=historical,
    )
