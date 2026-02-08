# BVMT Anomaly Detection Service

This service provides an API for detecting anomalies in stock market data from the Bourse des Valeurs Mobilières de Tunis (BVMT). It is built with FastAPI and uses several statistical and machine learning techniques to identify unusual trading days.

## Features

-   **Anomaly Detection**: Analyzes historical stock data to find anomalies based on trading volume, price changes, and transaction patterns.
-   **Flexible Queries**: Allows specifying a company stock code and a date range for analysis.
-   **Configurable Algorithms**: The parameters for anomaly detection (e.g., thresholds, rolling windows, model parameters) are easily configurable.
-   **RESTful API**: Exposes a simple and clean API to get anomaly reports.

## API Endpoints

### `GET /health`

Returns the health status of the service.

-   **Response:**
    ```json
    {
      "status": "ok",
      "service": "anomaly-detection"
    }
    ```

### `GET /anomalies`

Runs the anomaly detection pipeline for a given company and date range.

-   **Query Parameters:**
    -   `code` (str, required): The stock code of the company (e.g., "PX1").
    -   `start` (str, required): The start date for the analysis in `YYYY-MM-DD` format.
    -   `end` (str, required): The end date for the analysis in `YYYY-MM-DD` format.

-   **Success Response:** A JSON report containing per-day anomaly details and summary statistics.

-   **Error Response:**
    -   `400 Bad Request`: If required query parameters are missing.
    -   `500 Internal Server Error`: If the anomaly detection process fails for any reason.

### `GET /config`

Exposes the current non-secret configuration of the anomaly detection algorithms for debugging purposes.

## Technology Stack

-   **Backend**: Python, FastAPI
-   **Database**: PostgreSQL (via `asyncpg`)
-   **Data Science**: Pandas, NumPy, Scikit-learn
-   **Server**: Uvicorn

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd backend/services/anomaly_detection
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The service is configured via environment variables. You can create a `.env` file in the project root to store them.

-   `DATABASE_URL`: The connection string for the PostgreSQL database.
    -   Default: A public Neon.tech database URL.
-   `HOST`: The host on which the service will run.
    -   Default: `0.0.0.0`
-   `PORT`: The port for the service.
    -   Default: `8001`

Other algorithm-specific parameters can be tuned directly in `config.py`.

## Running the Service

To run the service locally, use uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

The `--reload` flag enables hot-reloading for development.

## Example Usage

You can query the `/anomalies` endpoint using `curl` or any API client:

```bash
curl "http://localhost:8001/anomalies?code=BIAT&start=2023-01-01&end=2023-03-31"
```
