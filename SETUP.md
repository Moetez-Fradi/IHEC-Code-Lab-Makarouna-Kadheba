# Carthage Alpha - Setup Guide for Team

## Quick Start (Team Members)

### 1. Clone the Repository

```bash
git clone https://github.com/Moetez-Fradi/IHEC-Code-Lab-Makarouna-Kadheba.git
cd IHEC-Code-Lab-Makarouna-Kadheba
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy 'psycopg[binary]' python-dotenv pydantic pydantic-settings loguru pandas

# Copy environment file
cp .env.example .env

# Database is already set up on Neon (no local PostgreSQL needed!)
```

### 3. Start Backend

```bash
# From backend directory with venv activated
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Visit: http://localhost:8000/docs for API documentation

### 4. Frontend Setup

```bash
cd ui
npm install
npm run dev
```

Visit: http://localhost:3000

## Database Access

**We're using Neon PostgreSQL (cloud) - No local setup needed!**

All team members share the same database:

- Host: `ep-shy-breeze-ag2f4327-pooler.c-2.eu-central-1.aws.neon.tech`
- Database: `neondb`
- Connection string is in `backend/.env.example`

## Architecture

- **Backend**: FastAPI (Python) - Port 8000
- **Frontend**: Next.js 15 - Port 3000
- **Database**: Neon PostgreSQL 17 (cloud)
- **n8n**: Workflow automation - Port 5678

## API Endpoints

Base URL: `http://localhost:8000/api`

- `GET /stocks` - List all stocks
- `GET /stocks/{ticker}` - Stock details
- `GET /stocks/{ticker}/history` - Historical prices
- `GET /market/overview` - Market overview (TUNINDEX)
- `GET /predictions/{ticker}` - Price predictions
- `GET /sentiment/{ticker}` - Sentiment analysis
- `GET /anomalies` - Market anomalies
- `POST /portfolio/optimize` - Portfolio recommendations

## Team Responsibilities

1. **Backend & Orchestration**: FastAPI + n8n workflows
2. **Frontend**: Next.js dashboard
3. **ML - Prediction/Sentiment**: LSTM/TFT + MarBERT
4. **ML - Anomaly/Portfolio**: Isolation Forest + Portfolio optimization

## Need Help?

- API Docs: http://localhost:8000/docs
- Check README.md for detailed information
- Database is pre-loaded with historical data (2016-2025)
