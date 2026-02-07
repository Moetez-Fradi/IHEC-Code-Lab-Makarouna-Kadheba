"""Anomaly detection endpoints."""
from fastapi import APIRouter
from .predictions import anomalies_router

router = anomalies_router
