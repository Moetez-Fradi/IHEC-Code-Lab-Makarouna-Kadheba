# 🔮 Forecasting Service

> **LSTM-powered machine learning service for 5-day stock price predictions**

## 📋 Overview

The Forecasting Service uses LSTM (Long Short-Term Memory) neural networks to predict stock prices, trading volumes, and market liquidity for the next 5 business days. It provides confidence intervals and model validation metrics to assess prediction reliability.

## 🚀 Configuration

### Port
- **8008** (Production)

### Environment Variables

Create `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bvmt

# Model Parameters
LSTM_UNITS=50
DROPOUT_RATE=0.2
EPOCHS=50
BATCH_SIZE=32

# Forecasting Configuration
LOOKBACK_DAYS=60              # Days to use for training
FORECAST_DAYS=5               # Days to predict
CONFIDENCE_LEVEL=0.95         # 95% confidence interval
```

## 📦 Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## ▶️ Launch

```bash
# Development mode
python app.py

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8008 --workers 2
```

## 🛠️ API Endpoints

### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "forecasting",
  "model": "LSTM"
}
```

### Generate Forecast

```bash
GET /api/forecasting/forecast
```

**Query Parameters:**
- `code` (required): Stock ISIN code (e.g., "TN0001100254")
- `lookback` (optional): Historical days for training (default: 60)

**Example:**
```bash
curl "http://localhost:8008/api/forecasting/forecast?code=TN0001100254"
```

## 🔧 Technologies

- **TensorFlow/Keras** - Deep learning framework
- **FastAPI** - Web framework
- **scikit-learn** - Preprocessing and metrics
- **Pandas** - Data manipulation
- **asyncpg** - PostgreSQL async driver

-   **Error Responses**:
    -   `400 Bad Request`: If the `code` parameter is missing or if there is not enough historical data.
    -   `500 Internal Server Error`: If an unexpected error occurs during the forecasting process.

### `GET /config`

Exposes the current non-secret configuration of the service for debugging purposes.

## Setup and Installation

### Prerequisites

-   Python 3.10+
-   A running PostgreSQL database instance.

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd IHEC-Code-Lab-Makarouna-Kadheba/backend/services/forecasting
```

### 2. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies.

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install all required packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

The service is configured via environment variables. Create a `.env` file in the project root or set them in your shell:

```
# main.py, service.py
PORT=8002
HOST="0.0.0.0"

# db.py
DATABASE_URL="postgresql://user:password@hostname:5432/database_name"

# config.py
FORECAST_HORIZON=5
MIN_HISTORY_DAYS=100
DEFAULT_LOOKBACK_DAYS=500
XGB_N_ESTIMATORS=100
XGB_MAX_DEPTH=4
# ... and other model hyperparameters
```

## Running the Service

You can run the application using `uvicorn`. For development, the `--reload` flag will automatically restart the server on code changes.

```bash
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

The service will be available at `http://localhost:8002`.

## Machine Learning Models

The service does not rely on pre-trained, static models. Instead, it trains new models for each request, ensuring that the forecasts are based on the most up-to-date data.

-   **Price & Volume Forecasting**: `xgboost.XGBRegressor` is used to predict the closing price and volume for each of the next 5 days. A separate model is trained for each day in the horizon.
-   **Liquidity Classification**: `sklearn.ensemble.RandomForestClassifier` is used to predict the probability of high or low liquidity. Liquidity is defined as "high" if the daily volume exceeds its 20-day rolling median.
-   **Feature Engineering**: A rich set of over 40 features is generated from the raw OHLCV data, including:
    -   Lagged prices and returns
    -   Moving averages (MA, EMA)
    -   Technical indicators (MACD, RSI, Bollinger Bands)
    -   Volatility measures
    -   Calendar features (day of week, month)
