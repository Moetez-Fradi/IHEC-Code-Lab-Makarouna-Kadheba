"""SHAP‑based explainability for the PPO agent."""

import logging

import numpy as np
import shap

logger = logging.getLogger(__name__)


def _predict_fn(model, observations: np.ndarray) -> np.ndarray:
    """Wrapper that returns action arrays for SHAP."""
    actions = []
    for obs in observations:
        a, _ = model.predict(obs, deterministic=True)
        actions.append(a)
    return np.array(actions)


def explain(model, sample_obs: np.ndarray, feature_names: list[str] | None = None) -> dict:
    """Compute SHAP values for the most recent observation.

    Parameters
    ----------
    model : stable_baselines3 model with .predict()
    sample_obs : (n_samples, state_dim) background data
    feature_names : optional labels for each state dimension
    """
    background = sample_obs[:min(50, len(sample_obs))]
    explainer = shap.KernelExplainer(
        lambda x: _predict_fn(model, x),
        background,
    )
    latest = sample_obs[-1:]
    values = explainer.shap_values(latest, nsamples=100)

    # values may be a list of arrays (one per output action dim)
    if isinstance(values, list):
        # Average SHAP importance across all output dimensions
        vals = np.mean([np.abs(v[0]) for v in values], axis=0)
    else:
        v = values[0]
        vals = np.abs(v) if v.ndim == 1 else np.mean(np.abs(v), axis=-1)

    n = len(vals)
    names = feature_names or [f"f{i}" for i in range(n)]
    ranked = sorted(zip(names, vals.tolist()), key=lambda x: abs(x[1]), reverse=True)

    return {
        "top_features": [{"name": n, "impact": v} for n, v in ranked[:10]],
        "raw_values": dict(ranked),
    }
