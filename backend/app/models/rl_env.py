"""
rl_env.py — Custom Gymnasium environment for the PPO trading agent.
Observation: [rf_prob_up, lstm_pct, sentiment, rsi_norm, position, pnl_norm]
Actions: 0=SELL, 1=HOLD, 2=BUY
Reward: risk-adjusted return (Sharpe-like)
"""
import gymnasium as gym
import numpy as np
from gymnasium import spaces
import logging

logger = logging.getLogger(__name__)

ACTION_LABELS = {0: "SELL", 1: "HOLD", 2: "BUY"}


class TradingEnv(gym.Env):
    """
    Paper trading environment where PPO learns from fused signals.

    Observation space (6 dims):
        0: rf_prob_up      — RF probability of upward move [0, 1] -> [-1,1]
        1: lstm_pct        — LSTM predicted % change, normalized [-1, 1]
        2: sentiment       — VADER compound score [-1, 1]
        3: rsi_norm        — RSI normalized to [-1, 1]
        4: position        — current position: -1, 0, 1
        5: pnl_norm        — running P&L normalized [-1, 1]
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, price_series: np.ndarray, signals: list):
        super().__init__()
        self.price_series = price_series
        self.signals = signals
        self.T = min(len(price_series), len(signals))

        self.observation_space = spaces.Box(
            low=np.array([-1.0] * 6, dtype=np.float32),
            high=np.array([1.0] * 6, dtype=np.float32),
        )
        self.action_space = spaces.Discrete(3)

        self.reset()

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.step_idx = 0
        self.position = 0
        self.cash = 10000.0
        self.entry_price = 0.0
        self.total_pnl = 0.0
        self.returns_history = []
        return self._get_obs(), {}

    def _get_obs(self) -> np.ndarray:
        sig = self.signals[self.step_idx] if self.step_idx < len(self.signals) else {}
        rf = float(sig.get("rf_prob_up", 0.5)) * 2 - 1
        lstm = float(np.clip(sig.get("lstm_pct", 0.0) / 5.0, -1.0, 1.0))
        sent = float(np.clip(sig.get("sentiment", 0.0), -1.0, 1.0))
        rsi = float((sig.get("rsi", 50.0) - 50.0) / 50.0)
        pos = float(self.position)
        pnl_norm = float(np.clip(self.total_pnl / 1000.0, -1.0, 1.0))
        return np.array([rf, lstm, sent, rsi, pos, pnl_norm], dtype=np.float32)

    def step(self, action: int):
        if self.step_idx >= self.T - 1:
            return self._get_obs(), 0.0, True, False, {}

        price_now = self.price_series[self.step_idx]
        price_next = self.price_series[self.step_idx + 1]
        actual_return = (price_next - price_now) / price_now

        reward = 0.0
        if action == 2:
            if self.position <= 0:
                self.position = 1
                self.entry_price = price_now
            reward = actual_return * 100
        elif action == 0:
            if self.position >= 0:
                if self.position == 1 and self.entry_price > 0:
                    pnl = (price_now - self.entry_price) / self.entry_price
                    reward = pnl * 100
                    self.total_pnl += pnl * self.cash
                self.position = -1
        else:
            if self.position == 1:
                reward = actual_return * 50

        if action != 1:
            reward -= 0.1

        self.returns_history.append(reward)
        self.step_idx += 1
        done = self.step_idx >= self.T - 1
        return self._get_obs(), float(reward), done, False, {}


def make_training_env(price_series: np.ndarray, signals: list):
    """Factory for creating a TradingEnv."""
    return TradingEnv(price_series, signals)
