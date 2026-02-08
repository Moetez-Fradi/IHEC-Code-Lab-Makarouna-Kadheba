"""FastAPI application entrypoint for the forecasting service."""

from fastapi import FastAPI
from .routes import router

app = FastAPI(
    title="Forecasting Service",
    description=(
        "Probabilistic price & liquidity forecasting for BVMT securities.\n\n"
        "Includes quantile forecasts, hybrid liquidity model, transfer learning, "
        "synthetic augmentation, SHAP explainability, and execution triggers."
    ),
    version="1.0.0",
)

app.include_router(router, prefix="/api/forecasting")
