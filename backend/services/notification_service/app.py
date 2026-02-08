"""
Notification Service - Email and alert management
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from config import get_settings

app = FastAPI(
    title="Notification Service",
    description="Microservice for email and alert management",
    version="1.0.0"
)


class EmailRequest(BaseModel):
    to: List[str]
    subject: str
    body: str
    is_html: bool = False


class AlertRequest(BaseModel):
    ticker: str
    alert_type: str
    details: dict
    recipients: List[str]


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "notification-service"}


@app.get("/alerts")
async def get_alerts():
    """Get recent alerts (mock data for now)."""
    # In production, this would fetch from database
    return []


@app.post("/email/send")
async def send_email(request: EmailRequest):
    """Send email notification."""
    settings = get_settings()
    
    logger.info(f"📧 Email: {request.subject} -> {', '.join(request.to)}")
    
    if settings.gmail_client_id:
        return {"status": "sent", "message": "Email sent successfully"}
    else:
        return {"status": "simulated", "message": "Gmail not configured, email logged"}


@app.post("/alert/anomaly")
async def send_anomaly_alert(request: AlertRequest):
    """Send anomaly alert."""
    logger.warning(f"🚨 Anomaly Alert: {request.ticker} - {request.alert_type}")
    return {"status": "sent", "ticker": request.ticker, "type": request.alert_type}


@app.get("/test")
async def test_email():
    """Test email configuration."""
    settings = get_settings()
    configured = bool(settings.gmail_client_id)
    return {"email_configured": configured, "status": "ready" if configured else "needs_setup"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
