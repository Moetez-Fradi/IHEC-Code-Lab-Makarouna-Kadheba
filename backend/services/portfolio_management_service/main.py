"""FastAPI application entrypoint."""

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

app = FastAPI(
    title="Portfolio Management Service",
    description="Dual‑agent RL portfolio optimiser for the Tunisian market",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
