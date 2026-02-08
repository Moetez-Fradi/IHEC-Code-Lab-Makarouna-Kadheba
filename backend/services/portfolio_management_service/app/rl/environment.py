"""Gymnasium portfolio environment (Agent B perspective)."""

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from app.core.config import settings
from app.core.types import StressType
from app.data.preprocessor import build_state_vector
from app.rl.rewards import defender_reward


class PortfolioEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, price_matrix: np.ndarray, macro: dict, n_assets: int = 0,
                 initial_capital: float | None = None, tx_cost: float | None = None, lookback: int = 20):
        super().__init__()
        self.prices = price_matrix
        self.macro = macro
        self.n_assets = n_assets or price_matrix.shape[1]
        self.initial_capital = initial_capital or settings.INITIAL_CAPITAL
        self.tx_cost = tx_cost if tx_cost is not None else settings.TRANSACTION_COST
        self.lookback = lookback
        self.max_steps = len(price_matrix) - lookback - 1

        state_dim = 3 * self.n_assets + len(macro) + 1
        self.observation_space = spaces.Box(-np.inf, np.inf, (state_dim,), np.float32)
        self.action_space = spaces.Box(0.0, 1.0, (self.n_assets,), np.float32)
        self._reset_state()

    def _reset_state(self):
        self.step_idx = self.lookback
        self.weights = np.ones(self.n_assets) / self.n_assets
        self.value = self.initial_capital
        self.stress = 0.0
        self.history = [self.value]
        sd = self.observation_space.shape[0]
        self.observation_buffer = np.zeros((0, sd))

    def _vol(self) -> np.ndarray:
        if self.step_idx < self.lookback:
            return np.full(self.n_assets, 0.15)
        w = self.prices[self.step_idx - self.lookback : self.step_idx]
        return (np.diff(w, axis=0) / (w[:-1] + 1e-8)).std(axis=0)

    def _obs(self) -> np.ndarray:
        return build_state_vector(self.weights, self.prices[self.step_idx], self._vol(), self.macro, self.stress)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self._reset_state()
        obs = self._obs()
        self.observation_buffer = obs.reshape(1, -1)
        return obs, {"value": self.value}

    def step(self, action: np.ndarray):
        action = np.abs(action)
        action /= action.sum() + 1e-8
        cost = np.sum(np.abs(action - self.weights)) * self.tx_cost * self.value
        self.weights = action
        self.step_idx += 1

        ret = self._portfolio_return()
        self.value = self.value * (1 + ret) - cost
        vol = self._vol().mean()
        reward = defender_reward(ret, vol, self.stress)

        self.history.append(self.value)
        done = self.step_idx >= self.max_steps
        obs = self._obs()
        self.observation_buffer = np.vstack([self.observation_buffer, obs.reshape(1, -1)])
        info = {"value": self.value, "return": ret, "vol": vol, "weights": self.weights.tolist()}
        return obs, reward, done, False, info

    def _portfolio_return(self) -> float:
        prev, curr = self.prices[self.step_idx - 1], self.prices[self.step_idx]
        return float(np.dot(self.weights, (curr - prev) / (prev + 1e-8)))

    def inject_stress(self, kind: StressType, intensity: float):
        self.stress = float(np.clip(intensity, 0, 1))
        s = self.step_idx
        if kind == StressType.SECTOR_CRASH:
            self.prices[s:] *= (1 - intensity)
        elif kind == StressType.INTEREST_RATE_SPIKE:
            self.macro["policy_rate"] = self.macro.get("policy_rate", settings.BCT_POLICY_RATE) * (1 + intensity)
            self.prices[s:] *= (1 - intensity * 0.5)
        elif kind == StressType.CURRENCY_DEPRECIATION:
            fallback_fx = 3.1  # TND/USD approximate
            self.macro["exchange_rate_usd"] = self.macro.get("exchange_rate_usd", fallback_fx) * (1 + intensity)
