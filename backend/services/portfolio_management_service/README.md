# 💼 Portfolio Management Service

> **Advanced portfolio management with risk analysis, backtesting, and performance tracking**

## 📋 Overview

The Portfolio Management Service provides comprehensive portfolio tracking, performance analysis, risk metrics, and rebalancing recommendations. It extends the Portfolio Service with management features like holdings tracking, transaction history, and performance attribution.

## 🚀 Configuration

### Port
- **8011** (Production)

### Environment Variables

Create `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bvmt

# Service URLs
PORTFOLIO_SERVICE_URL=http://localhost:8007
STOCK_SERVICE_URL=http://localhost:8001
MARKET_SERVICE_URL=http://localhost:8002

# Portfolio Settings
DEFAULT_CURRENCY=TND
ENABLE_MULTI_CURRENCY=false
ENABLE_FRACTIONAL_SHARES=false

# Risk Management
MAX_POSITION_SIZE=0.25        # 25% max per stock
MAX_SECTOR_EXPOSURE=0.40      # 40% max per sector
STOP_LOSS_DEFAULT=0.10        # 10% stop loss
TAKE_PROFIT_DEFAULT=0.20      # 20% take profit

# Performance Tracking
BENCHMARK_INDEX=TUNINDEX
REBALANCE_FREQUENCY=quarterly
ENABLE_TAX_TRACKING=true
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
pandas==2.1.4
numpy==1.26.3
scipy==1.12.0
plotly==5.18.0
streamlit==1.30.0
uvicorn==0.27.0
```

## ▶️ Launch

```bash
# API Server
python main.py

# Streamlit Dashboard (optional)
streamlit run streamlit_app.py --server.port 8501
```

## 🛠️ API Endpoints

### Portfolio Management

```bash
POST /api/portfolios              # Create portfolio
GET  /api/portfolios              # List user portfolios
GET  /api/portfolios/{id}         # Get portfolio details
PUT  /api/portfolios/{id}         # Update portfolio
DELETE /api/portfolios/{id}       # Delete portfolio
```

### Holdings

```bash
GET  /api/portfolios/{id}/holdings          # Current holdings
POST /api/portfolios/{id}/holdings          # Add position
PUT  /api/portfolios/{id}/holdings/{stock}  # Update position
DELETE /api/portfolios/{id}/holdings/{stock} # Remove position
```

### Transactions

```bash
GET  /api/portfolios/{id}/transactions      # Transaction history
POST /api/portfolios/{id}/transactions/buy  # Record buy
POST /api/portfolios/{id}/transactions/sell # Record sell
POST /api/portfolios/{id}/transactions/dividend # Record dividend
```

### Performance

```bash
GET /api/portfolios/{id}/performance        # Overall performance
GET /api/portfolios/{id}/performance/daily  # Daily returns
GET /api/portfolios/{id}/performance/vs-benchmark # Compare to TUNINDEX
GET /api/portfolios/{id}/attribution        # Performance attribution
```

### Risk Metrics

```bash
GET /api/portfolios/{id}/risk               # Risk metrics (VaR, Sharpe, etc.)
GET /api/portfolios/{id}/correlation        # Correlation matrix
GET /api/portfolios/{id}/stress-test        # Stress testing results
```

### Rebalancing

```bash
GET  /api/portfolios/{id}/rebalance/check   # Check if rebalance needed
POST /api/portfolios/{id}/rebalance/recommend # Get rebalance recommendations
POST /api/portfolios/{id}/rebalance/execute # Execute rebalance
```

## 📊 Response Examples

### Portfolio Details

```json
{
  "id": 123,
  "name": "Growth Portfolio",
  "user_id": 456,
  "created_at": "2025-01-15T10:00:00Z",
  "currency": "TND",
  "initial_value": 50000,
  "current_value": 54250,
  "cash_balance": 5000,
  "invested_value": 49250,
  "total_return": 4250,
  "total_return_pct": 8.5,
  "holdings_count": 8,
  "last_rebalanced": "2026-01-01T00:00:00Z",
  "risk_profile": "moderate"
}
```

### Holdings

```json
{
  "holdings": [
    {
      "symbol": "BNA",
      "name": "Banque Nationale Agricole",
      "shares": 500,
      "avg_cost": 8.00,
      "current_price": 8.25,
      "cost_basis": 4000,
      "current_value": 4125,
      "unrealized_gain": 125,
      "unrealized_gain_pct": 3.12,
      "weight": 8.38,
      "sector": "Banques",
      "last_updated": "2026-02-08T10:30:00Z"
    }
  ],
  "summary": {
    "total_cost_basis": 49250,
    "total_current_value": 54250,
    "total_unrealized_gain": 5000,
    "total_return_pct": 10.15
  }
}
```

### Performance Metrics

```json
{
  "period": "1_year",
  "metrics": {
    "total_return": 8.5,
    "annualized_return": 8.5,
    "volatility": 12.3,
    "sharpe_ratio": 0.68,
    "sortino_ratio": 0.95,
    "max_drawdown": -8.2,
    "calmar_ratio": 1.04,
    "beta": 0.85,
    "alpha": 2.1,
    "information_ratio": 0.42,
    "tracking_error": 5.0
  },
  "vs_benchmark": {
    "benchmark": "TUNINDEX",
    "benchmark_return": 6.4,
    "outperformance": 2.1,
    "correlation": 0.78
  }
}
```

### Risk Analysis

```json
{
  "value_at_risk": {
    "var_95": -1250,
    "var_99": -2100,
    "cvar_95": -1580
  },
  "portfolio_stats": {
    "expected_return": 0.085,
    "volatility": 0.123,
    "sharpe_ratio": 0.68
  },
  "concentration": {
    "herfindahl_index": 0.142,
    "effective_number_stocks": 7.04,
    "top_3_concentration": 0.48
  },
  "sector_exposure": {
    "Banques": 0.35,
    "Industrie": 0.25,
    "Services": 0.20,
    "Assurances": 0.15,
    "Autres": 0.05
  }
}
```

## 🔧 Features

### 1. Portfolio Tracking
- Real-time holdings valuation
- Transaction history
- Cost basis tracking
- Dividend reinvestment

### 2. Performance Analysis
- Time-weighted returns (TWR)
- Money-weighted returns (IRR)
- Benchmark comparison
- Attribution analysis

### 3. Risk Management
- Value at Risk (VaR)
- Maximum Drawdown
- Beta and correlation
- Stress testing

### 4. Rebalancing
- Drift detection
- Rebalance recommendations
- Tax-efficient rebalancing
- Automatic execution

### 5. Reporting
- Portfolio statements
- Tax reports
- Performance reports
- Risk reports

## 📈 Streamlit Dashboard

Access the visual dashboard at `http://localhost:8501`

**Features:**
- Portfolio overview
- Interactive charts
- Holdings table
- Performance graphs
- Risk metrics
- Rebalance simulator

## 🔧 Technologies

- **FastAPI** - REST API
- **SQLAlchemy** - Database ORM
- **Pandas** - Data analysis
- **NumPy/SciPy** - Numerical computations
- **Plotly** - Interactive charts
- **Streamlit** - Dashboard UI

## 📝 Project Structure

```
portfolio_management_service/
├── main.py                    # FastAPI application
├── streamlit_app.py          # Streamlit dashboard
├── app/
│   ├── models/
│   │   ├── portfolio.py      # Portfolio model
│   │   ├── holding.py        # Holding model
│   │   └── transaction.py    # Transaction model
│   ├── services/
│   │   ├── portfolio_service.py
│   │   ├── performance_service.py
│   │   ├── risk_service.py
│   │   └── rebalance_service.py
│   ├── routes/
│   │   ├── portfolios.py
│   │   ├── holdings.py
│   │   ├── transactions.py
│   │   └── analytics.py
│   └── utils/
│       ├── calculations.py
│       └── validators.py
├── tests/
├── requirements.txt
└── README.md
```

## 🐛 Debugging

```bash
# Create test portfolio
curl -X POST http://localhost:8011/api/portfolios \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Portfolio", "initial_value": 10000}'

# View portfolio
curl http://localhost:8011/api/portfolios/1

# Check logs
tail -f logs/portfolio_management.log
```

## 📊 Performance

- **Latency**: <200ms for most endpoints
- **Portfolio Valuation**: Real-time
- **Risk Calculations**: ~500ms
- **Concurrent Users**: 100+

---

**Maintained by:** Makarouna Kadheba - IHEC CodeLab 2.0
