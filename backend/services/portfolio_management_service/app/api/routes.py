"""FastAPI route handlers."""

import numpy as np
from fastapi import APIRouter, HTTPException

from app.api import schemas
from app.core.config import settings
from app.core.types import StressType
from app.data import macro, stock_loader, features, preprocessor
from app.explainability import shap_explain, interpreter
from app.portfolio import metrics as pm
from app.portfolio.tracker import Portfolio
from app.rl.agents.trainer import Trainer
from app.rl.environment import PortfolioEnv

router = APIRouter()

# ── module‑level state (initialised on first call) ───────────
_state: dict = {}


def _init():
    """Lazy‑load data & build env on first request."""
    if _state:
        return
    raw = stock_loader.load_all(settings.DATA_DIR, settings.TUNISIAN_TICKERS)
    if raw is None or raw.empty:
        raw = stock_loader.generate_placeholder(settings.TUNISIAN_TICKERS)
    enriched = features.enrich(raw)
    macro_snap = macro.fetch_macro_snapshot()

    price_cols = [c for c in enriched.columns if c.endswith("_close")]
    price_matrix = enriched[price_cols].values

    env = PortfolioEnv(price_matrix, macro_snap, n_assets=len(price_cols))
    trainer = Trainer(env)
    portfolio = Portfolio(tickers=settings.TUNISIAN_TICKERS)

    _state.update(
        env=env, trainer=trainer, portfolio=portfolio,
        price_matrix=price_matrix, macro=macro_snap,
        enriched=enriched, price_cols=price_cols,
    )
