"""Agent B – Portfolio optimiser (PPO)."""

import logging
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

from app.core.config import settings
from app.rl.environment import PortfolioEnv

logger = logging.getLogger(__name__)


class _ProgressCB(BaseCallback):
    def _on_step(self) -> bool:
        return True


class Optimizer:
    def __init__(self, env: PortfolioEnv, lr: float | None = None, model_path: str | None = None):
        self.env = env
        self.path = model_path or f"{settings.MODEL_DIR}/agent_b"
        self.model = PPO(
            "MlpPolicy", env,
            learning_rate=lr or settings.RL_LEARNING_RATE,
            n_steps=2048, batch_size=64, n_epochs=10,
            gamma=settings.RL_GAMMA, gae_lambda=0.95,
            clip_range=0.2, ent_coef=0.01,
            verbose=0,
        )
        self._try_load()

    # ── public API ────────────────────────────────────────────

    def train(self, timesteps: int = 100_000):
        logger.info("Training Agent B for %d steps …", timesteps)
        self.model.learn(total_timesteps=timesteps, callback=_ProgressCB())
        self.save()

    def predict(self, state: np.ndarray, deterministic: bool = True) -> np.ndarray:
        action, _ = self.model.predict(state, deterministic=deterministic)
        action = np.abs(action)
        return action / (action.sum() + 1e-8)

    def evaluate(self, n_episodes: int = 5) -> dict:
        rewards, values = [], []
        for _ in range(n_episodes):
            obs, _ = self.env.reset()
            total_r, done = 0.0, False
            while not done:
                obs, r, done, _, info = self.env.step(self.predict(obs))
                total_r += r
            rewards.append(total_r)
            values.append(info["value"])
        return {"mean_reward": float(np.mean(rewards)), "mean_value": float(np.mean(values))}

    # ── persistence ───────────────────────────────────────────

    def save(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.model.save(self.path)

    def _try_load(self):
        if Path(f"{self.path}.zip").exists():
            self.model = PPO.load(self.path, env=self.env)
            logger.info("Loaded Agent B from %s", self.path)
