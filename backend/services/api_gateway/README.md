# 🌐 API Gateway Service

> **Centralized entry point and routing service for all BVMT microservices**

## 📋 Overview

The API Gateway acts as the single entry point for all frontend requests. It routes traffic to the appropriate microservices, handles authentication, implements rate limiting, and provides a unified API interface.

## 🚀 Configuration

### Port
- **8000** (Production)

### Environment Variables

Create `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bvmt

# Security
SECRET_KEY=your-super-secret-jwt-key-here

# CORS
CORS_ORIGINS=http://localhost:3000

# Microservices URLs
STOCK_SERVICE_URL=http://localhost:8001
MARKET_SERVICE_URL=http://localhost:8002
NOTIFICATION_SERVICE_URL=http://localhost:8003
ANOMALY_SERVICE_URL=http://localhost:8004
SENTIMENT_SERVICE_URL=http://localhost:8005
AUTH_SERVICE_URL=http://localhost:8006
PORTFOLIO_SERVICE_URL=http://localhost:8007
FORECASTING_SERVICE_URL=http://localhost:8008
CHATBOT_SERVICE_URL=http://localhost:8009
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
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000
```

## 🛠️ API Routes

### Health Check
```bash
GET /health
```

### Stock Routes
```bash
GET  /api/stocks              # List all stocks
GET  /api/stocks/{symbol}     # Get stock details
GET  /api/stocks/{symbol}/history  # Historical data
```

### Market Routes
```bash
GET /api/market/overview      # Market statistics
GET /api/market/latest        # Latest market data
```

### Forecasting Routes
```bash
GET  /api/forecasting/forecast?code={isin}  # 5-day forecast
```

### Anomaly Routes
```bash
GET  /api/anomalies?code={isin}&start={date}&end={date}
```

## 🔧 Technologies

- **FastAPI** - Web framework
- **httpx** - Async HTTP client
- **uvicorn** - ASGI server
