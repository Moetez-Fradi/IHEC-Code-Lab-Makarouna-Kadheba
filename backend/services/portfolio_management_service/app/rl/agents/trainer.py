"""Orchestrates adversarial training of Agent A vs Agent B."""

import logging

from app.rl.agents.adversary import Adversary
from app.rl.agents.optimizer import Optimizer
from app.rl.environment import PortfolioEnv

logger = logging.getLogger(__name__)


class Trainer:
    def __init__(self, env: PortfolioEnv):
        self.env = env
        self.optimizer = Optimizer(env)
        self.adversary = Adversary()

    def quick_train(self, timesteps: int = 50_000):
        """Train Agent B only (fastest path for hackathon)."""
        self.optimizer.train(timesteps)
        result = self.optimizer.evaluate()
        logger.info("Quick‑train result: %s", result)
        return result

    def adversarial_train(self, rounds: int = 5, timesteps: int = 20_000):
        """Alternate: train B → stress with A → repeat."""
        for i in range(1, rounds + 1):
            logger.info("=== Round %d / %d ===", i, rounds)
            self.optimizer.train(timesteps)

            # Run a few adversarial episodes
            for _ in range(3):
                obs, _ = self.env.reset()
                done = False
                while not done:
                    stress = self.adversary.generate(obs, self.env.n_assets)
                    self.env.inject_stress(stress["type"], stress["intensity"])
                    action = self.optimizer.predict(obs, deterministic=False)
                    obs, _, done, _, _ = self.env.step(action)

        self.optimizer.save()
        return self.optimizer.evaluate()
