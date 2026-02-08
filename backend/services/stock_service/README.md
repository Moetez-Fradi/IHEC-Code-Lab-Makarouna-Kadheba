# Stock Service

Microservice for stock data operations.

## Endpoints

- `GET /health` - Health check
- `GET /stocks` - List all stocks
- `GET /stocks/{ticker}` - Get stock by ticker
- `GET /stocks/{ticker}/history` - Get historical prices

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app:app --reload --port 8001
```
