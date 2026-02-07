# Carthage Alpha - Intelligent Trading Assistant for BVMT

**IHEC CODELAB 2.0 Hackathon Project**

Carthage Alpha is an intelligent trading assistant for the Tunisian Stock Exchange (BVMT) that combines price prediction, sentiment analysis, anomaly detection, and portfolio optimization using AI/ML.

## 🏗️ Architecture

- **Frontend**: Next.js 16 with TypeScript and Tailwind CSS
- **Backend**: FastAPI (Python) with SQLAlchemy
- **Database**: PostgreSQL 16 with TimescaleDB
- **Orchestration**: n8n for workflow automation
- **Cache**: Redis (optional)
- **Deployment**: Docker Compose

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- 8GB RAM minimum
- 20GB free disk space

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/Moetez-Fradi/IHEC-Code-Lab-Makarouna-Kadheba.git
cd IHEC-Code-Lab-Makarouna-Kadheba
```

2. **Configure environment variables**

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

3. **Start all services**

```bash
 docker-compose up -d
```

4. **Wait for services to be healthy (2-3 minutes)**

```bash
docker-compose ps
```

5. **Load historical data**

```bash
docker-compose exec backend python scripts/load_data.py
```

### Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **n8n Workflow UI**: http://localhost:5678 (admin/admin123)
- **PostgreSQL**: localhost:5432 (postgres/postgres)

## 📁 Project Structure

```
.
├── backend/                 # FastAPI backend
│   ├── api/                # API endpoints
│   │   ├── endpoints/      # Route handlers
│   │   └── schemas.py      # Pydantic models
│   ├── core/               # Core functionality
│   │   ├── config.py       # Configuration
│   │   ├── database.py     # DB connection
│   │   └── models.py       # SQLAlchemy models
│   ├── services/           # Business logic
│   ├── main.py             # FastAPI app
│   └── requirements.txt    # Python dependencies
├── ui/                     # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/         # React components
│   └── lib/               # Utilities
├── n8n_workflows/          # Automation workflows
│   ├── market_pulse.json   # News scraping
│   └── anomaly_monitor.json # Alert system
├── notebooks/              # Jupyter notebooks
├── data/                   # Historical data
├── database/               # Database schemas
└── docker-compose.yml      # Docker orchestration
```

## 🎯 Features

### Module 1: Price Prediction

- 5-day price forecasting using LSTM/TFT models
- Confidence intervals for predictions
- Liquidity classification

### Module 2: Sentiment Analysis

- Tunisian dialect (Arabizi) support with MarBERT
- Multi-source news aggregation
- Real-time sentiment tracking

### Module 3: Anomaly Detection

- Volume spike detection (>3σ)
- Price manipulation identification
- CMF regulatory compliance alerts

### Module 4: Portfolio Management

- Risk-based portfolio optimization
- Explainable AI (SHAP) recommendations
- Performance metrics (ROI, Sharpe, Drawdown)

## 🔧 Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development

```bash
cd ui
npm install
npm run dev
```

### n8n Workflows

1. Access n8n at http://localhost:5678
2. Import workflows from `n8n_workflows/`
3. Configure credentials (PostgreSQL, Telegram, Email)
4. Activate workflows

## 📊 API Endpoints

- `GET /api/stocks` - List all BVMT stocks
- `GET /api/stocks/{ticker}` - Stock details
- `GET /api/stocks/{ticker}/history` - Historical prices
- `GET /api/market/overview` - Market overview (TUNINDEX)
- `GET /api/predictions/{ticker}` - Price predictions
- `GET /api/sentiment/{ticker}` - Sentiment analysis
- `GET /api/anomalies` - Market anomalies
- `POST /api/portfolio/optimize` - Portfolio recommendations

## 👥 Team

- **Person 1**: Backend & n8n Orchestration
- **Person 2**: Frontend & UI/UX
- **Person 3**: ML - Prediction & Sentiment
- **Person 4**: ML - Anomaly & Portfolio + DevOps

##License

MIT License - IHEC CODELAB 2.0

## 📞 Support

For questions or issues, contact the team or create an issue on GitHub.

---

**Built with ❤️ for IHEC CODELAB 2.0 Hackathon**
