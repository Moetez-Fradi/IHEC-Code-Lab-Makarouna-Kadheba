# API Gateway

Main entry point for all API requests. Routes to appropriate microservices.

## Endpoints

### Health

- `GET /health` - Health check

### Stocks

- `GET /api/stocks` - List all stocks
- `GET /api/stocks/{ticker}` - Get stock details
- `GET /api/stocks/{ticker}/history` - Get historical prices

### Market

- `GET /api/market/overview` - Market statistics
- `GET /api/market/gainers` - Top gainers
- `GET /api/market/losers` - Top losers
- `GET /api/market/volume` - Trading volume

### ML (Placeholders)

- `GET /api/predictions/{ticker}` - Price predictions
- `GET /api/sentiment/{ticker}` - Sentiment analysis
- `GET /api/anomalies` - Anomaly detection

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app:app --reload --port 8000
```
