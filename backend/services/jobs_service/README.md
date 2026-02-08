# 🔄 Jobs Service

> **Background job scheduling and processing service for BVMT automation**

## 📋 Overview

The Jobs Service manages scheduled tasks and background jobs for the BVMT platform. It handles periodic data updates, report generation, anomaly detection scans, and automated notifications using APScheduler.

## 🚀 Configuration

### Port
- **8010** (Optional - for job monitoring API)

### Environment Variables

Create `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bvmt

# Job Configuration
ENABLE_SCHEDULER=true
TIMEZONE=Africa/Tunis

# Service URLs
STOCK_SERVICE_URL=http://localhost:8001
MARKET_SERVICE_URL=http://localhost:8002
ANOMALY_SERVICE_URL=http://localhost:8004
SENTIMENT_SERVICE_URL=http://localhost:8005
NOTIFICATION_SERVICE_URL=http://localhost:8003

# Job Intervals (minutes)
MARKET_PULSE_INTERVAL=15
ANOMALY_CHECK_INTERVAL=60
SENTIMENT_SCAN_INTERVAL=30

# Report Schedule (cron format)
DAILY_REPORT_TIME=18:00
WEEKLY_REPORT_DAY=friday
WEEKLY_REPORT_TIME=17:00
```

## 📦 Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Key Dependencies

```
apscheduler==3.10.4
fastapi==0.109.0
httpx==0.26.0
sqlalchemy==2.0.25
asyncpg==0.29.0
uvicorn==0.27.0
```

## ▶️ Launch

```bash
# Development mode
python app.py

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8010
```

## 🔧 Scheduled Jobs

### 1. Market Pulse (Every 15 minutes)

**Schedule:** `*/15 * * * *` (During trading hours: 9:00-16:00)

**Tasks:**
- Fetch latest stock prices from BVMT
- Update market indices (TUNINDEX, TUNINDEX20)
- Calculate sector performance
- Identify top gainers/losers

**Endpoint Triggered:** `POST /api/stocks/refresh`

### 2. Anomaly Detection Scan (Hourly)

**Schedule:** `0 * * * *` (Every hour)

**Tasks:**
- Scan all 82 BVMT stocks for anomalies
- Detect volume spikes (>3x average)
- Identify unusual price movements (>5%)
- Flag suspicious patterns
- Send alerts for critical anomalies

**Endpoint Triggered:** `POST /api/anomalies/batch`

### 3. Sentiment Analysis (Every 30 minutes)

**Schedule:** `*/30 * * * *`

**Tasks:**
- Scrape financial news websites
- Analyze social media sentiment (Tunizi/Arabizi)
- Update sentiment scores
- Generate heatmap data

**Endpoint Triggered:** `POST /api/sentiment/scrape`

### 4. Daily Market Report (18:00)

**Schedule:** `0 18 * * *` (After market close)

**Tasks:**
- Generate comprehensive daily report
- Calculate day's performance metrics
- Create charts and visualizations
- Email report to subscribers
- Archive report to database

**Contents:**
- Market summary (volume, cap, top movers)
- Sector performance breakdown
- Anomalies detected
- Sentiment analysis summary
- Tomorrow's calendar events

### 5. Weekly Performance Report (Friday 17:00)

**Schedule:** `0 17 * * 5`

**Tasks:**
- Weekly performance analysis
- Portfolio recommendations
- Risk assessment
- Market outlook

### 6. Database Cleanup (Daily 03:00)

**Schedule:** `0 3 * * *`

**Tasks:**
- Clean old logs (>90 days)
- Archive old notifications
- Optimize database indexes
- Vacuum PostgreSQL tables

## 🛠️ API Endpoints

### Job Management

```bash
GET  /api/jobs              # List all scheduled jobs
GET  /api/jobs/{job_id}     # Get job details
POST /api/jobs/{job_id}/run # Trigger job manually
POST /api/jobs/{job_id}/pause   # Pause job
POST /api/jobs/{job_id}/resume  # Resume job
```

### Job History

```bash
GET /api/jobs/history              # All job executions
GET /api/jobs/{job_id}/history     # Job-specific history
GET /api/jobs/history/failed       # Failed executions
```

### Reports

```bash
GET  /api/reports                  # List generated reports
GET  /api/reports/{report_id}      # Download report
POST /api/reports/generate         # Generate report on-demand
```

## 📊 Job Monitoring

### Job Status Response

```json
{
  "jobs": [
    {
      "id": "market_pulse",
      "name": "Market Pulse Update",
      "schedule": "*/15 * * * *",
      "status": "running",
      "next_run": "2026-02-08T10:15:00Z",
      "last_run": "2026-02-08T10:00:00Z",
      "last_status": "success",
      "execution_time_ms": 1250,
      "success_count": 145,
      "failure_count": 2
    }
  ]
}
```

## 🔧 Technologies

- **APScheduler** - Job scheduling framework
- **FastAPI** - Monitoring API
- **httpx** - HTTP client for service calls
- **SQLAlchemy** - Database ORM
- **Celery** (optional) - Distributed task queue

## 📝 Project Structure

```
jobs_service/
├── app.py                 # Main application
├── jobs/
│   ├── market_pulse.py    # Market data updates
│   ├── anomaly_scan.py    # Anomaly detection
│   ├── sentiment_scan.py  # Sentiment analysis
│   ├── reports.py         # Report generation
│   └── cleanup.py         # Database cleanup
├── scheduler/
│   ├── config.py          # Schedule configurations
│   └── manager.py         # Job management
├── utils/
│   ├── http_client.py     # Service communication
│   └── notifications.py   # Alert sending
├── requirements.txt
└── README.md
```

## 🐛 Debugging

```bash
# View job logs
tail -f logs/jobs.log

# Test job manually
curl -X POST http://localhost:8010/api/jobs/market_pulse/run

# Check job status
curl http://localhost:8010/api/jobs
```

## 📈 Performance

- **Market Pulse**: ~1-2s execution time
- **Anomaly Scan**: ~15-30s (82 stocks)
- **Daily Report**: ~5-10s generation
- **Concurrent Jobs**: Up to 5 simultaneous

---

**Maintained by:** Makarouna Kadheba - IHEC CodeLab 2.0
