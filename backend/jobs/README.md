# Background Jobs - Python Replacement for n8n

This directory contains Python scripts that replace the n8n workflows.
These are easier to debug, test, and modify than no-code workflows.

## Jobs

### 1. Market Pulse (`market_pulse.py`)

**Replaces:** `n8n_workflows/market_pulse.json`

**What it does:**

- Scrapes financial news from IlBoursa and other sources
- Analyzes sentiment using NLP (placeholder until ML team implements)
- Stores sentiment data in database
- Sends alerts for extreme sentiment

**Run manually:**

```bash
cd backend
source venv/bin/activate
python jobs/market_pulse.py
```

**Customize:**

- Add more news sources in `self.news_sources`
- Adjust sentiment threshold in `run()` method
- Enable Telegram by setting `self.telegram_enabled = True`

### 2. Anomaly Handler (`anomaly_handler.py`)

**Replaces:** `n8n_workflows/anomaly_monitor.json`

**What it does:**

- Receives anomaly alerts from ML detection service
- Logs anomalies to database
- Sends notifications based on severity (Telegram, Email)
- Routes CRITICAL anomalies to CMF

**Use from ML code:**

```python
from jobs.anomaly_handler import AnomalyAlertHandler

handler = AnomalyAlertHandler()
handler.handle_anomaly({
    'stock_id': 5,
    'ticker': 'SFBT',
    'anomaly_type': 'VOLUME_SPIKE',
    'severity': 'HIGH',
    'score': 3.5,
    'description': 'Volume 350% above average'
})
```

**Test:**

```bash
python jobs/anomaly_handler.py
```

### 3. Scheduler (`scheduler.py`)

**Replaces:** n8n schedule triggers

**What it does:**

- Runs Market Pulse every 15 minutes
- Generates daily reports at 3:30 PM
- Easy to add more scheduled jobs

**Run in background:**

```bash
source venv/bin/activate
python jobs/scheduler.py &
```

**Production (systemd):**

```bash
sudo systemctl start carthage-scheduler
```

## Setup

### Install Dependencies

```bash
pip install schedule beautifulsoup4 requests
```

### Enable Notifications

**Telegram:**

1. Get bot token from @BotFather
2. Set `self.telegram_enabled = True` in jobs
3. Add Telegram API integration

**Email:**

1. Configure SMTP settings
2. Set `self.email_enabled = True`
3. Add email sending code

## Production Deployment

### Option 1: Systemd Service

Create `/etc/systemd/system/carthage-scheduler.service`:

```ini
[Unit]
Description=Carthage Alpha Job Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/python jobs/scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl enable carthage-scheduler
sudo systemctl start carthage-scheduler
```

### Option 2: Docker

Add to `docker-compose.yml`:

```yaml
scheduler:
  build: ./backend
  command: python jobs/scheduler.py
  environment:
    - DATABASE_URL=${DATABASE_URL}
  depends_on:
    - backend
```

### Option 3: Cron

Add to crontab:

```bash
*/15 * * * * cd /path/to/backend && venv/bin/python jobs/market_pulse.py
30 15 * * * cd /path/to/backend && venv/bin/python jobs/daily_report.py
```

## Advantages over n8n

✅ **Version Control:** Git-friendly Python code
✅ **Debugging:** Use breakpoints, print statements, logging
✅ **Testing:** Write unit tests easily
✅ **AI Assistance:** Easier for AI to read/modify Python
✅ **No Extra Service:** No need to run n8n container
✅ **Dependencies:** Just Python libraries
✅ **Flexibility:** Full Python power for complex logic

## Migration Complete! 🎉

The n8n workflows have been successfully converted to Python.
You can now delete or keep `n8n_workflows/` as reference.
