# BVMT Forecasting Service

This service provides 5-day forecasts for stock prices, trading volume, and market liquidity for securities listed on the Bourse de Tunis (BVMT). It uses an on-the-fly training approach with XGBoost and RandomForest models to generate predictions.

## Features

-   **Price Forecasting**: Predicts the closing price for the next 5 business days.
-   **Confidence Intervals**: Provides upper and lower bounds for price predictions.
-   **Volume Forecasting**: Predicts the expected trading volume for each day.
-   **Liquidity Prediction**: Classifies the expected liquidity as "high" or "low" with a corresponding probability.
-   **On-the-Fly Training**: Models are trained in real-time using the latest available historical data for any given stock.
-   **REST API**: Simple and easy-to-use API built with FastAPI.

## Technology Stack

-   **Backend**: Python, FastAPI
-   **Machine Learning**: XGBoost, Scikit-learn, Pandas, Numpy
-   **Database**: PostgreSQL (for historical data, via `asyncpg`)
-   **Server**: Uvicorn

## API Endpoints

### `GET /health`

Returns the health status of the service.

-   **Response**:
    ```json
    {
      "status": "ok",
      "service": "forecasting"
    }
    ```

### `GET /forecast`

Generates and returns a 5-day forecast for a specific stock.

-   **Query Parameters**:
    -   `code` (required, string): The stock's ISIN code (e.g., `TN0001100254`).
    -   `lookback` (optional, integer): The number of historical days to use for training. Defaults to `500`.

-   **Example Request**:
    ```bash
    curl "http://localhost:8002/forecast?code=TN0001100254"
    ```

-   **Successful Response (200 OK)**:
    Returns a detailed forecast report including daily predictions, model validation metrics, and historical data for charting.

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
