"""Individual endpoint handlers — imported by routes.py."""

import numpy as np
from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    HealthResponse, TrainRequest, TrainResponse,
    RecommendRequest, RecommendResponse,
    SimulateRequest, SimulateResponse,
    StressRequest, StressResponse,
    PortfolioResponse, MacroResponse,
)
from app.api.routes import _init, _state
from app.core.config import settings
from app.core.types import RiskProfile, StressType
from app.data import macro
from app.explainability import shap_explain, interpreter
from app.portfolio import metrics as pm
from app.portfolio.profile import adjust_weights, profile_description
from app.portfolio.simulator import simulate

router = APIRouter()


def _parse_profile(raw: str) -> RiskProfile:
    try:
        return RiskProfile(raw.lower())
    except ValueError:
        raise HTTPException(400, f"Unknown profile: {raw}. Use conservateur|modere|agressif")


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@router.post("/train", response_model=TrainResponse)
def train(req: TrainRequest):
    _init()
    t = _state["trainer"]
    if req.adversarial:
        result = t.adversarial_train(rounds=req.rounds, timesteps=req.timesteps)
    else:
        result = t.quick_train(timesteps=req.timesteps)
    return TrainResponse(**result)


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    _init()
    profile = _parse_profile(req.profile)
    env, opt = _state["env"], _state["trainer"].optimizer
    obs, _ = env.reset()
    raw_weights = opt.predict(obs)

    # Per-asset annualised volatility for profile adjustment
    prices = _state["price_matrix"]
    returns = np.diff(prices, axis=0) / prices[:-1]
    vols = np.std(returns, axis=0) * np.sqrt(252)
    weights = adjust_weights(raw_weights, profile, vols)

    tickers = settings.TUNISIAN_TICKERS[: env.n_assets]
    w_dict = dict(zip(tickers, weights.tolist()))

    port_returns = (returns * weights).sum(axis=1)
    met = pm.compute_all(port_returns)

    shap_res = shap_explain.explain(opt.model, env.observation_buffer)
    prof_desc = profile_description(profile)
    expl = interpreter.interpret(shap_res, w_dict, prof_desc, met)

    return RecommendResponse(
        profile=profile.value,
        weights=w_dict,
        metrics=met,
        explanation=expl,
    )


@router.post("/simulate", response_model=SimulateResponse)
def simulate_portfolio(req: SimulateRequest):
    _init()
    profile = _parse_profile(req.profile)
    env, opt = _state["env"], _state["trainer"].optimizer
    obs, _ = env.reset()
    raw_weights = opt.predict(obs)

    prices = _state["price_matrix"]
    returns = np.diff(prices, axis=0) / prices[:-1]
    vols = np.std(returns, axis=0) * np.sqrt(252)
    weights = adjust_weights(raw_weights, profile, vols)

    result = simulate(weights, prices, capital=req.capital, days=req.days)
    result["profile"] = profile.value
    return SimulateResponse(**result)


@router.post("/stress-test", response_model=StressResponse)
def stress_test(req: StressRequest):
    _init()
    env, opt = _state["env"], _state["trainer"].optimizer
    try:
        kind = StressType(req.stress_type)
    except ValueError:
        raise HTTPException(400, f"Unknown stress type: {req.stress_type}")

    obs, _ = env.reset()
    pre = {"value": float(_state["portfolio"].value(_state["price_matrix"][-1]))}
    env.inject_stress(kind, req.intensity)
    obs, _, _, _, info = env.step(opt.predict(obs))
    post = {"value": info["value"]}
    return StressResponse(pre_stress=pre, post_stress=post, impact=post["value"] - pre["value"])


@router.get("/portfolio", response_model=PortfolioResponse)
def portfolio():
    _init()
    prices = _state["price_matrix"][-1]
    return PortfolioResponse(**_state["portfolio"].snapshot(prices))


@router.get("/macro", response_model=MacroResponse)
def macro_data():
    return MacroResponse(data=macro.fetch_macro_snapshot())
