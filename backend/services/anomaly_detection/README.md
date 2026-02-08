# 🚨 Anomaly Detection Service

> **Machine Learning service for detecting unusual patterns in BVMT stock data**

## 📋 Overview

The Anomaly Detection Service uses Isolation Forest and statistical methods to identify unusual trading patterns in the Tunisian stock market. It analyzes price movements, volume spikes, and trading behavior to detect potential market manipulation, unusual volatility, or significant events.

## 🚀 Configuration

### Port
- **8004** (Production)

### Environment Variables

Create `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bvmt

# Model Parameters
CONTAMINATION_RATE=0.1          # Expected % of anomalies (10%)
N_ESTIMATORS=100                # Number of trees in Isolation Forest
RANDOM_STATE=42

# Detection Thresholds
PRICE_CHANGE_THRESHOLD=0.05     # 5% price change
VOLUME_SPIKE_THRESHOLD=3.0      # 3x average volume
Z_SCORE_THRESHOLD=3.0           # 3 standard deviations

# Cache
ENABLE_CACHE=true
CACHE_TTL=3600                  # 1 hour
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
uvicorn app:app --host 0.0.0.0 --port 8004 --workers 2
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
  "service": "anomaly-detection",
  "version": "1.0.0"
}
```

### Detect Anomalies

```bash
GET /api/anomalies
```

**Query Parameters:**
- `code` (required): Stock ISIN code
- `start` (required): Start date (YYYY-MM-DD)
- `end` (required): End date (YYYY-MM-DD)

**Example:**
```bash
curl "http://localhost:8004/api/anomalies?code=TN0001100254&start=2025-01-01&end=2026-02-08"
```

## 🔧 Technologies

- **FastAPI** - Web framework
- **scikit-learn** - Isolation Forest ML
- **Pandas** - Data manipulation
- **NumPy** - Numerical computations
- **asyncpg** - PostgreSQL async driver
- **uvicorn** - ASGI server

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
