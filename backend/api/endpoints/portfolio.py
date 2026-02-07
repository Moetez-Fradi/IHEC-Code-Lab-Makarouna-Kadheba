"""Portfolio management endpoints."""
from fastapi import APIRouter
from .predictions import portfolio_router

router = portfolio_router
