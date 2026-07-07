"""
rl_agent.py — Stable-Baselines3 PPO agent for trade decisions.
Train, save, load, and run inference with the PPO policy.
"""
import os
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "../../checkpoints")
ACTION_LABELS = {0: "SELL", 1: "HOLD", 2: "BUY"}


def train_ppo(price_series: np.ndarray, signals: list,
              total_timesteps: int = 50000, ticker: str = "multi"):
    """Train PPO on the custom TradingEnv. Returns trained model."""
    from stable_baselines3 import PPO
    from .rl_env import make_training_env

    env = make_training_env(price_series, signals)
    model = PPO(
        "MlpPolicy",
        env,
        verbose=0,
        learning_rate=3e-4,
        n_steps=512,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.01,
    )
    model.learn(total_timesteps=total_timesteps, progress_bar=False)
    logger.info(f"PPO training complete for {ticker}: {total_timesteps} steps")
    return model


def save_ppo(model, ticker: str = "multi") -> str:
    """Save PPO model checkpoint."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CHECKPOINT_DIR, f"ppo_{ticker}_{ts}")
    model.save(path)
    logger.info(f"PPO saved: {path}.zip")
    return path


def load_ppo(ticker: str = "multi"):
    """Load the most recent PPO checkpoint."""
    from stable_baselines3 import PPO

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    candidates = [
        f for f in os.listdir(CHECKPOINT_DIR)
        if f.startswith(f"ppo_{ticker}") and f.endswith(".zip")
    ]
    if not candidates:
        logger.warning(f"No PPO checkpoint found for {ticker}")
        return None
    candidates.sort()
    path = os.path.join(CHECKPOINT_DIR, candidates[-1][:-4])
    model = PPO.load(path)
    logger.info(f"PPO loaded: {path}")
    return model


def ppo_predict(model, observation: np.ndarray) -> dict:
    """
    Run PPO inference.
    observation: (6,) array [rf, lstm_pct, sentiment, rsi, position, pnl]
    Returns action label and confidence.
    """
    if model is None:
        rf_signal = observation[0]
        lstm_signal = observation[1]
        sentiment = observation[2]
        score = 0.4 * rf_signal + 0.4 * lstm_signal + 0.2 * sentiment
        action = 2 if score > 0.1 else (0 if score < -0.1 else 1)
        return {
            "action": ACTION_LABELS[action],
            "action_id": action,
            "confidence": abs(score),
            "source": "heuristic",
        }

    obs_tensor = observation.reshape(1, -1).astype(np.float32)
    action, _ = model.predict(obs_tensor, deterministic=True)
    action_id = int(action.item())

    try:
        import torch
        with torch.no_grad():
            obs_t = torch.tensor(obs_tensor)
            dist = model.policy.get_distribution(obs_t)
            probs = dist.distribution.probs.numpy()[0]
            confidence = float(probs[action_id])
    except Exception:
        confidence = 0.7

    return {
        "action": ACTION_LABELS[action_id],
        "action_id": action_id,
        "confidence": round(confidence, 4),
        "source": "ppo",
    }
