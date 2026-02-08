# Market Service

Microservice for market statistics and analytics.

## Endpoints

- `GET /health` - Health check
- `GET /overview` - Market overview with TUNINDEX
- `GET /gainers` - Top gaining stocks
- `GET /losers` - Top losing stocks

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app:app --reload --port 8002
```
