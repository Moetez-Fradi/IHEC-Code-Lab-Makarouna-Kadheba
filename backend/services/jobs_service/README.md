# Jobs Service

Background job scheduling and processing service.

## Jobs

- **Market Pulse** - Fetch and analyze market news (every 15 min)
- **Anomaly Detection** - Detect price/volume anomalies (hourly)
- **Daily Report** - Generate daily market summary (18:00)

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```
