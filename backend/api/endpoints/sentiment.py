"""Sentiment analysis endpoints."""
from fastapi import APIRouter
from .predictions import sentiment_router

router = sentiment_router
