"""Tests for RL environment, rewards, and agents."""

import numpy as np
import pytest

from app.core.types import StressType
from app.rl.rewards import defender_reward, adversary_reward
from app.rl.environment import PortfolioEnv
from app.rl.agents.adversary import Adversary


def _make_env(n_assets=3, steps=100):
    macro = {"gdp": 2.0, "inf": 5.0, "rate": 8.0}
    prices = 100 + np.cumsum(np.random.randn(steps, n_assets) * 0.5, axis=0)
    return PortfolioEnv(prices, macro, n_assets=n_assets)


class TestRewards:
    def test_defender_positive_return(self):
        r = defender_reward(0.05, 0.15, 0.0)
        assert r > 0

    def test_defender_stress_penalty(self):
        r_no = defender_reward(0.01, 0.1, 0.0)
        r_stress = defender_reward(0.01, 0.1, 0.5)
        assert r_stress < r_no

    def test_adversary_reward_on_loss(self):
        r = adversary_reward(100_000, 95_000)
        assert r > 0

    def test_adversary_reward_on_gain(self):
        r = adversary_reward(100_000, 105_000)
        assert r < 0


class TestEnvironment:
    def test_reset_returns_obs(self):
        env = _make_env()
        obs, info = env.reset()
        assert obs.shape == env.observation_space.shape
        assert info["value"] == env.initial_capital

    def test_step_returns_tuple(self):
        env = _make_env()
        env.reset()
        action = env.action_space.sample()
        result = env.step(action)
        assert len(result) == 5
        obs, reward, done, trunc, info = result
        assert obs.shape == env.observation_space.shape
        assert isinstance(reward, float)
        assert "value" in info

    def test_episode_terminates(self):
        env = _make_env(steps=50)
        obs, _ = env.reset()
        done = False
        steps = 0
        while not done:
            obs, _, done, _, _ = env.step(env.action_space.sample())
            steps += 1
        assert steps > 0
        assert done

    def test_inject_stress_sector_crash(self):
        env = _make_env()
        env.reset()
        old_prices = env.prices[env.step_idx:].copy()
        env.inject_stress(StressType.SECTOR_CRASH, 0.2)
        assert np.all(env.prices[env.step_idx:] < old_prices)

    def test_observation_buffer_grows(self):
        env = _make_env()
        env.reset()
        assert env.observation_buffer.shape[0] == 1
        env.step(env.action_space.sample())
        assert env.observation_buffer.shape[0] == 2


class TestAdversary:
    def test_generate_returns_dict(self):
        adv = Adversary()
        state = np.random.rand(10)
        result = adv.generate(state, n_assets=3)
        assert "type" in result
        assert "intensity" in result
        assert isinstance(result["type"], StressType)
        assert 0.0 < result["intensity"] < 1.0
