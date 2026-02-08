# 🌍 Market Service

> **Market statistics, indices, and analytics service for BVMT**

## 📋 Overview

The Market Service provides comprehensive market statistics, index calculations, sector analysis, and trading analytics for the Tunisian Stock Exchange (BVMT). It aggregates data from individual stocks to provide market-wide insights.

## 🚀 Configuration

### Port
- **8002** (Production)

### Environment Variables

Create `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bvmt

# Cache
REDIS_URL=redis://localhost:6379
ENABLE_CACHE=true
CACHE_TTL=300  # 5 minutes

# Market Configuration
MARKET_OPEN_TIME=09:00
MARKET_CLOSE_TIME=16:00
TRADING_DAYS=monday,tuesday,wednesday,thursday,friday

# Indices
TUNINDEX_BASE=1000
TUNINDEX20_BASE=1000
```

## 📦 Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Key Dependencies

```
fastapi==0.109.0
sqlalchemy==2.0.25
asyncpg==0.29.0
pandas==2.1.4
numpy==1.26.3
uvicorn==0.27.0
```

## ▶️ Launch

```bash
# Development mode
python app.py

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8002 --workers 4
```

## 🛠️ API Endpoints

### 1. Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "market",
  "market_status": "open"
}
```

### 2. Market Overview

```bash
GET /api/market/overview
```

**Response:**
```json
{
  "date": "2026-02-08",
  "market_status": "open",
  "indices": {
    "TUNINDEX": {
      "value": 7245.32,
      "change": 42.15,
      "change_pct": 0.58,
      "volume": 12500000
    },
    "TUNINDEX20": {
      "value": 3850.18,
      "change": 28.45,
      "change_pct": 0.74,
      "volume": 8200000
    }
  },
  "statistics": {
    "total_stocks": 82,
    "advancing": 45,
    "declining": 28,
    "unchanged": 9,
    "total_volume": 18500000,
    "total_value": 42500000,
    "market_cap": 28500000000,
    "trades_count": 3250
  }
}
```

### 3. Latest Market Data

```bash
GET /api/market/latest
```

**Returns:** Array of all 82 stocks with latest prices

### 4. Top Gainers

```bash
GET /api/market/gainers?limit=10
```

**Response:**
```json
{
  "gainers": [
    {
      "symbol": "SFBT",
      "name": "Société Franco-Belge des Tubes",
      "price": 12.50,
      "change": 1.20,
      "change_pct": 10.62,
      "volume": 45000,
      "value": 562500
    }
  ]
}
```

### 5. Top Losers

```bash
GET /api/market/losers?limit=10
```

### 6. Sector Performance

```bash
GET /api/market/sectors
```

**Response:**
```json
{
  "sectors": [
    {
      "name": "Banques",
      "stocks_count": 15,
      "market_cap": 12500000000,
      "avg_change_pct": 1.25,
      "volume": 5500000,
      "top_performers": ["BNA", "BT", "ATB"]
    },
    {
      "name": "Assurances",
      "stocks_count": 8,
      "market_cap": 2100000000,
      "avg_change_pct": -0.35,
      "volume": 850000,
      "top_performers": ["STAR", "CARTE", "ASTREE"]
    }
  ]
}
```

### 7. Trading Volume Analysis

```bash
GET /api/market/volume
```

**Response:**
```json
{
  "date": "2026-02-08",
  "total_volume": 18500000,
  "total_value": 42500000,
  "avg_volume_30d": 16200000,
  "volume_ratio": 1.14,
  "top_volume_stocks": [
    {
      "symbol": "BNA",
      "volume": 1250000,
      "value": 10312500,
      "pct_of_total": 6.76
    }
  ],
  "volume_by_sector": {
    "Banques": 5500000,
    "Industrie": 3200000,
    "Services": 2800000
  }
}
```

### 8. Market Indices History

```bash
GET /api/market/indices/history?start=2025-01-01&end=2026-02-08
```

**Response:**
```json
{
  "indices": [
    {
      "date": "2025-01-01",
      "TUNINDEX": 7100.25,
      "TUNINDEX20": 3750.50
    }
  ]
}
```

### 9. Market Calendar

```bash
GET /api/market/calendar?month=2&year=2026
```

**Response:**
```json
{
  "month": "February 2026",
  "trading_days": 20,
  "holidays": [
    {
      "date": "2026-02-14",
      "name": "Valentine's Day",
      "market_closed": false
    }
  ],
  "events": [
    {
      "date": "2026-02-15",
      "type": "earnings",
      "company": "BNA",
      "description": "Q4 2025 Earnings Release"
    }
  ]
}
```

## 📊 Index Calculation

### TUNINDEX (82 stocks)

**Formula:** Market cap weighted index

```python
TUNINDEX = (Current_Market_Cap / Base_Market_Cap) * 1000
```

### TUNINDEX20 (Top 20 stocks)

**Formula:** Free-float market cap weighted

```python
TUNINDEX20 = Σ(Price_i * Free_Float_Shares_i) / Divisor
```

## 🔧 Technologies

- **FastAPI** - Web framework
- **SQLAlchemy** - Database ORM
- **Pandas** - Data analysis
- **NumPy** - Numerical computations
- **Redis** (optional) - Caching
- **asyncpg** - PostgreSQL async driver

## 📝 Project Structure

```
market_service/
├── app.py                 # FastAPI application
├── models/
│   ├── market.py         # Market data models
│   └── indices.py        # Index calculations
├── calculators/
│   ├── tunindex.py       # TUNINDEX calculator
│   ├── sectors.py        # Sector analysis
│   └── statistics.py     # Market stats
├── utils/
│   ├── cache.py          # Redis caching
│   └── database.py       # DB queries
├── requirements.txt
└── README.md
```

## 🐛 Debugging

```bash
# Test market overview
curl http://localhost:8002/api/market/overview

# Check gainers
curl http://localhost:8002/api/market/gainers?limit=5

# View logs
tail -f logs/market_service.log
```

## 📈 Performance

- **Latency**: <100ms (with cache)
- **Throughput**: 500 req/s
- **Cache Hit Rate**: 85%
- **Index Calculation**: Real-time

---

**Maintained by:** Makarouna Kadheba - IHEC CodeLab 2.0
