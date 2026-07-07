"""
agent.py — Signal fusion, trade decision, and plain-English reasoning generator.
This is the X factor: four models feeding sequentially into a final decision
with a human-readable explanation for every trade.
"""
import numpy as np
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def build_observation(rf_result: dict, lstm_result: dict, sentiment_result: dict,
                       features: dict, position: int, pnl_norm: float) -> np.ndarray:
    """
    Build the 6-dim observation vector for PPO from upstream model outputs.
    Sequential pipeline: RF -> LSTM -> Sentiment -> [PPO input]
    """
    rf_prob_up = rf_result.get("prob_up", 0.5)
    lstm_pct = lstm_result.get("predicted_pct", 0.0)
    sentiment = sentiment_result.get("sentiment_score", 0.0)
    rsi = features.get("rsi", 50.0)

    rf_norm = rf_prob_up * 2 - 1
    lstm_norm = np.clip(lstm_pct / 5.0, -1.0, 1.0)
    sent_norm = np.clip(sentiment, -1.0, 1.0)
    rsi_norm = (rsi - 50.0) / 50.0

    return np.array([rf_norm, lstm_norm, sent_norm, rsi_norm, float(position), pnl_norm],
                    dtype=np.float32)


def generate_reason(ticker: str, rf_result: dict, lstm_result: dict,
                     sentiment_result: dict, features: dict, rl_result: dict,
                     action: str) -> str:
    """
    Generate a plain-English trading reason — the column that gets screenshotted.
    """
    rsi = features.get("rsi", 50.0)
    macd = features.get("macd", 0.0)
    macd_signal = features.get("macd_signal", 0.0)
    bb_pct = features.get("bb_pct", 0.5)
    volume_ratio = features.get("volume_ratio", 1.0)

    rf_dir = rf_result.get("direction", "HOLD")
    rf_prob = rf_result.get("prob_up", 0.5)
    rf_conf = rf_result.get("confidence", "LOW")

    lstm_close = lstm_result.get("predicted_close", 0.0)
    lstm_pct = lstm_result.get("predicted_pct", 0.0)

    sent_score = sentiment_result.get("sentiment_score", 0.0)
    sent_label = sentiment_result.get("score_label", "NEUTRAL")
    top_headlines = sentiment_result.get("top_headlines", [])

    ppo_confidence = rl_result.get("confidence", 0.0)

    parts = []

    if abs(lstm_pct) > 0.1:
        direction_word = "upside" if lstm_pct > 0 else "downside"
        parts.append(
            f"LSTM projects {abs(lstm_pct):.2f}% {direction_word} "
            f"(target close: ${lstm_close:.2f})"
        )

    rf_pct = rf_prob * 100
    if rf_conf == "HIGH":
        parts.append(
            f"RF signals {rf_dir} momentum with {rf_pct:.0f}% probability "
            f"(RSI {rsi:.0f}, {'MACD crossover' if macd > macd_signal else 'MACD below signal'})"
        )
    else:
        parts.append(
            f"RF shows weak {rf_dir} signal ({rf_pct:.0f}% probability, RSI {rsi:.0f})"
        )

    if bb_pct < 0.2:
        parts.append("Price near lower Bollinger Band — potential mean reversion")
    elif bb_pct > 0.8:
        parts.append("Price near upper Bollinger Band — extended, watch for reversal")

    if volume_ratio > 1.5:
        parts.append(f"Volume {volume_ratio:.1f}x above average — strong conviction")
    elif volume_ratio < 0.6:
        parts.append("Below-average volume — low conviction move")

    if abs(sent_score) > 0.05:
        headline_summary = ""
        if top_headlines:
            headline_summary = f' ("{top_headlines[0][:60]}...")'
        parts.append(f"News sentiment {sent_label} ({sent_score:+.2f}){headline_summary}")
    else:
        parts.append("Sentiment neutral — news not a factor")

    action_word = {"BUY": "confirms BUY", "SELL": "signals exit", "HOLD": "recommends HOLD"}.get(action, "decides HOLD")
    parts.append(f"RL policy {action_word} (confidence: {ppo_confidence:.0%})")

    return ". ".join(parts) + "."


def fuse_signals(ticker: str, rf_result: dict, lstm_result: dict,
                  sentiment_result: dict, features: dict, ppo_model,
                  portfolio_state: dict) -> dict:
    """
    Full sequential pipeline: RF -> LSTM -> Sentiment -> PPO observation -> action + reason.
    """
    position = portfolio_state.get("position", 0)
    pnl = portfolio_state.get("pnl_cumulative", 0.0)
    pnl_norm = float(np.clip(pnl / 5000.0, -1.0, 1.0))

    obs = build_observation(rf_result, lstm_result, sentiment_result,
                            features, position, pnl_norm)

    from .models.rl_agent import ppo_predict
    rl_result = ppo_predict(ppo_model, obs)
    action = rl_result["action"]

    reason = generate_reason(ticker, rf_result, lstm_result, sentiment_result,
                             features, rl_result, action)

    return {
        "ticker": ticker,
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "rf_direction": rf_result.get("direction", "HOLD"),
        "rf_prob_up": rf_result.get("prob_up", 0.5),
        "rf_confidence": rf_result.get("confidence", "LOW"),
        "lstm_predicted_close": lstm_result.get("predicted_close", 0.0),
        "lstm_predicted_pct": lstm_result.get("predicted_pct", 0.0),
        "sentiment_score": sentiment_result.get("sentiment_score", 0.0),
        "sentiment_label": sentiment_result.get("score_label", "NEUTRAL"),
        "rl_confidence": rl_result.get("confidence", 0.0),
        "rsi": features.get("rsi", 50.0),
        "macd": features.get("macd", 0.0),
        "reason": reason,
        "obs_vector": obs.tolist(),
    }
