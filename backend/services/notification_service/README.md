# Notification Service

Microservice for email and alert management.

## Endpoints

- `GET /health` - Health check
- `POST /email/send` - Send email
- `POST /alert/anomaly` - Send anomaly alert
- `GET /test` - Test email configuration

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app:app --reload --port 8003
```
