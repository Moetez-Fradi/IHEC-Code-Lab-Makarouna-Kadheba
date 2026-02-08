"""FastAPI router for the forecasting service."""

from fastapi import APIRouter, HTTPException

from .service import ForecastingService
from .schemas import (
    FeatureInput,
    ForecastOutput,
    ExplainOutput,
    RecommendOutput,
    AugmentRequest,
    AugmentOutput,
    TransferLearnRequest,
    TransferLearnOutput,
)

router = APIRouter()
service = ForecastingService()


@router.post(
    "/forecast",
    response_model=ForecastOutput,
    summary="Probabilistic price/liquidity forecast",
    tags=["Forecasting"],
)
def forecast_endpoint(features: FeatureInput):
    """
    Multi-horizon probabilistic price forecast (p10/p50/p90) combined
    with a liquidity-regime prediction.

    - **horizon**: 1–5 days
    - **history**: optional list of recent close prices for better accuracy
    - **order_book**: spread, depth, imbalance for the liquidity head
    """
    try:
        return service.predict(features.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/explain",
    response_model=ExplainOutput,
    summary="Forecast explainability (SHAP + CI)",
    tags=["Forecasting"],
)
def explain_endpoint(features: FeatureInput):
    """
    Returns SHAP values, confidence intervals, and top forecast drivers.
    """
    try:
        return service.explain_forecast(features.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/recommend",
    response_model=RecommendOutput,
    summary="Execution trigger recommendation",
    tags=["Forecasting"],
)
def recommend_endpoint(features: FeatureInput):
    """
    Combined price + liquidity signal producing enter / exit / hold / defer
    with timing advice (intraday, next_open, wait…).
    """
    try:
        return service.recommend_execution(features.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/augment",
    response_model=AugmentOutput,
    summary="Synthetic data augmentation",
    tags=["Forecasting"],
)
def augment_endpoint(req: AugmentRequest):
    """
    Generate synthetic price series (GAN / TS-VAE) to augment scarce
    data for illiquid BVMT securities.
    """
    try:
        return service.augment(
            price_history=req.price_history,
            n_synthetic=req.n_synthetic,
            method=req.method,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/transfer-learn",
    response_model=TransferLearnOutput,
    summary="Transfer learning (pre-train + fine-tune)",
    tags=["Forecasting"],
)
def transfer_learn_endpoint(req: TransferLearnRequest):
    """
    Pre-train on a cross-market / cross-sector corpus, then fine-tune
    on a single BVMT security.  The fine-tuned model becomes the active
    forecaster for subsequent /forecast calls.
    """
    try:
        return service.transfer_learn(
            target_prices=req.target_prices,
            source_corpus=req.source_corpus,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
