"""Pydantic request / response schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"


class TrainRequest(BaseModel):
    timesteps: int = 50_000
    adversarial: bool = False
    rounds: int = 5


class TrainResponse(BaseModel):
    mean_reward: float
    mean_value: float


class RecommendRequest(BaseModel):
    profile: str = "modere"  # conservateur | modere | agressif


class RecommendResponse(BaseModel):
    profile: str
    weights: dict[str, float]
    metrics: dict
    explanation: str


class SimulateRequest(BaseModel):
    profile: str = "modere"
    capital: float | None = None   # defaults to INITIAL_CAPITAL from settings
    days: int | None = None


class SimulateResponse(BaseModel):
    profile: str
    initial_capital: float
    final_value: float
    roi: float
    sharpe: float
    sortino: float
    max_drawdown: float
    volatility: float
    n_days: int
    daily_values: list[float]


class StressRequest(BaseModel):
    stress_type: str = "sector_crash"
    intensity: float = 0.20


class StressResponse(BaseModel):
    pre_stress: dict
    post_stress: dict
    impact: float


class PortfolioResponse(BaseModel):
    cash: float
    value: float
    weights: dict[str, float]
    n_transactions: int


class MacroResponse(BaseModel):
    data: dict
