"""
logger.py — Append-only trade logger to trades.csv.
Structured rows matching the PRD schema.
"""
import os
import csv
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
TRADES_CSV = os.path.join(DATA_DIR, "trades.csv")

FIELDNAMES = [
    "timestamp", "ticker", "action", "price_at_trade",
    "lstm_pred", "rf_direction", "sentiment_score",
    "rl_action", "reason", "position_size", "pnl_day", "pnl_cumulative",
]


def ensure_csv():
    """Create trades.csv with header if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(TRADES_CSV):
        with open(TRADES_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
        logger.info(f"Created trades.csv at {TRADES_CSV}")


def log_trade(ticker: str, action: str, price: float, signal: dict,
              execution: dict, portfolio_pnl: float):
    """Append a trade row to trades.csv."""
    ensure_csv()

    row = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker,
        "action": action,
        "price_at_trade": round(price, 2),
        "lstm_pred": signal.get("lstm_predicted_close", 0.0),
        "rf_direction": signal.get("rf_direction", "HOLD"),
        "sentiment_score": round(signal.get("sentiment_score", 0.0), 4),
        "rl_action": signal.get("action", "HOLD"),
        "reason": signal.get("reason", ""),
        "position_size": execution.get("position_value", 0.0),
        "pnl_day": execution.get("pnl", 0.0),
        "pnl_cumulative": round(portfolio_pnl, 2),
    }

    with open(TRADES_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)

    logger.info(f"Logged trade: {ticker} {action} @ ${price:.2f}")
    return row


def get_all_trades() -> list:
    """Read all trades from CSV. Returns list of dicts."""
    ensure_csv()
    trades = []
    try:
        with open(TRADES_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append(row)
    except Exception as e:
        logger.error(f"Error reading trades.csv: {e}")
    return trades


def get_trades_path() -> str:
    ensure_csv()
    return TRADES_CSV
