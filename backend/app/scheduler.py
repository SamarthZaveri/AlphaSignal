"""
scheduler.py — APScheduler managing the 60-second inference pipeline
and weekly model retraining.
"""
import logging
import asyncio
from datetime import datetime
from typing import Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_ws_broadcast: Optional[Callable] = None

state = {
    "last_run": None,
    "last_signals": {},
    "current_prices": {},
    "sentiment_cache": {},
    "models_loaded": False,
    "retrain_status": {
        "last_retrain": None,
        "next_retrain": None,
        "in_progress": False,
    },
    "metrics": {
        "rf_accuracy": {},
        "lstm_mae": {},
        "pnl_history": [],
    },
}

_models = {
    "rf": {},
    "lstm": {},
    "ppo": None,
}


def set_broadcast(fn: Callable):
    global _ws_broadcast
    _ws_broadcast = fn


def _to_python(obj):
    """Recursively convert numpy scalars to native Python types for JSON safety."""
    import numpy as np
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: _to_python(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_python(i) for i in obj]
    return obj


async def broadcast(data: dict):
    if _ws_broadcast:
        try:
            await _ws_broadcast(_to_python(data))
        except Exception as e:
            logger.error(f"Broadcast error: {e}")


def load_models():
    """Load all saved model checkpoints on startup."""
    from app.models.random_forest import load_rf
    from app.models.train_lstm import load_lstm
    from app.models.rl_agent import load_ppo
    from app.data.fetcher import ASSETS

    logger.info("Loading model checkpoints...")
    for ticker in ASSETS:
        rf = load_rf(ticker)
        if rf is None:
            rf = load_rf("multi")
        _models["rf"][ticker] = rf

        lstm = load_lstm(ticker)
        if lstm is None:
            lstm = load_lstm("multi")
        _models["lstm"][ticker] = lstm

    ppo = load_ppo("multi")
    _models["ppo"] = ppo

    state["models_loaded"] = True
    logger.info("Models loaded (None = will use heuristic fallback)")


async def run_pipeline():
    """
    Main 60-second pipeline:
    1. Fetch prices + features for all 5 assets
    2. Score sentiment
    3. Run RF -> LSTM -> PPO for each ticker
    4. Execute paper trades
    5. Log + broadcast
    """
    from app.data.fetcher import fetch_all_latest, ASSETS
    from app.data.features import compute_features, get_latest_features, get_feature_matrix, FEATURE_COLS
    from app.data.news import fetch_all_sentiment
    from app.models.random_forest import rf_predict
    from app.models.train_lstm import lstm_predict
    from app.models.rl_agent import ppo_predict
    from app.agent import build_observation, generate_reason
    from app.portfolio import get_portfolio
    from app.logger import log_trade
    import numpy as np

    logger.info("=== Pipeline run start ===")
    try:
        raw_data = fetch_all_latest()
        sentiment_data = fetch_all_sentiment()
        state["sentiment_cache"] = sentiment_data

        signals = {}
        prices = {}

        portfolio = get_portfolio()

        for ticker in ASSETS:
            df = raw_data.get(ticker)
            if df is None or df.empty:
                logger.warning(f"No data for {ticker}, skipping")
                continue

            df_feat = compute_features(df)
            if df_feat.empty:
                continue

            current_price = float(df_feat["close"].iloc[-1])
            prices[ticker] = current_price

            features_dict = get_latest_features(df_feat)
            sentiment = sentiment_data.get(ticker, {"sentiment_score": 0.0, "score_label": "NEUTRAL", "top_headlines": []})

            X, _ = get_feature_matrix(df_feat)
            rf_model = _models["rf"].get(ticker)
            if X.shape[0] > 0:
                rf_result = rf_predict(rf_model, X[-1:])
            else:
                rf_result = {"direction": "HOLD", "prob_up": 0.5, "confidence": "LOW"}

            lstm_model = _models["lstm"].get(ticker)
            available_features = [c for c in FEATURE_COLS if c in df_feat.columns]
            seq_data = df_feat[available_features].values
            if len(seq_data) >= 30:
                seq = seq_data[-30:]
                lstm_result = lstm_predict(lstm_model, seq, current_price)
            else:
                lstm_result = {"predicted_close": current_price, "predicted_pct": 0.0, "direction": "HOLD"}

            portfolio_state = portfolio.get_state(ticker)
            pnl_norm = float(np.clip(portfolio_state["pnl_cumulative"] / 5000.0, -1.0, 1.0))
            obs = build_observation(rf_result, lstm_result, sentiment, features_dict,
                                    portfolio_state["position"], pnl_norm)

            ppo_model = _models["ppo"]
            rl_result = ppo_predict(ppo_model, obs)
            action = rl_result["action"]

            reason = generate_reason(ticker, rf_result, lstm_result, sentiment,
                                     features_dict, rl_result, action)

            signal = {
                "ticker": ticker,
                "timestamp": datetime.utcnow().isoformat(),
                "price": current_price,
                "action": action,
                "rf_direction": rf_result["direction"],
                "rf_prob_up": rf_result["prob_up"],
                "rf_confidence": rf_result["confidence"],
                "lstm_predicted_close": lstm_result["predicted_close"],
                "lstm_predicted_pct": lstm_result["predicted_pct"],
                "sentiment_score": sentiment["sentiment_score"],
                "sentiment_label": sentiment["score_label"],
                "rl_confidence": rl_result["confidence"],
                "rsi": features_dict.get("rsi", 50.0),
                "macd": features_dict.get("macd", 0.0),
                "bb_pct": features_dict.get("bb_pct", 0.5),
                "volume_ratio": features_dict.get("volume_ratio", 1.0),
                "reason": reason,
                "top_headlines": sentiment.get("top_headlines", []),
            }
            signals[ticker] = signal

            execution = {}
            if action == "BUY":
                execution = portfolio.execute_buy(ticker, current_price)
                if execution.get("status") == "executed":
                    log_trade(ticker, "BUY", current_price, signal, execution, portfolio.pnl_cumulative)
            elif action == "SELL":
                execution = portfolio.execute_sell(ticker, current_price)
                if execution.get("status") == "executed":
                    log_trade(ticker, "SELL", current_price, signal, execution, portfolio.pnl_cumulative)

        state["last_run"] = datetime.utcnow().isoformat()
        state["last_signals"] = signals
        state["current_prices"] = prices

        portfolio_summary = portfolio.summary(prices)

        await broadcast({
            "type": "pipeline_update",
            "timestamp": state["last_run"],
            "signals": signals,
            "portfolio": portfolio_summary,
        })

        logger.info(f"=== Pipeline complete: {len(signals)} tickers processed ===")

    except Exception as e:
        logger.exception(f"Pipeline error: {e}")
        await broadcast({"type": "error", "message": str(e)})


async def run_retrain():
    """Weekly model retraining job."""
    from app.data.fetcher import fetch_all_historical, ASSETS
    from app.data.features import compute_features, get_feature_matrix, FEATURE_COLS
    from app.models.random_forest import train_rf, save_rf
    from app.models.train_lstm import train_lstm, save_lstm

    if state["retrain_status"]["in_progress"]:
        logger.warning("Retrain already in progress, skipping")
        return

    state["retrain_status"]["in_progress"] = True
    logger.info("=== Weekly retrain started ===")

    try:
        historical = fetch_all_historical()

        for ticker in ASSETS:
            df = historical.get(ticker)
            if df is None or df.empty:
                continue

            df_feat = compute_features(df)
            if df_feat.empty or len(df_feat) < 100:
                continue

            X, y = get_feature_matrix(df_feat)
            rf_model, rf_acc = train_rf(X, y, ticker)
            save_rf(rf_model, ticker)
            _models["rf"][ticker] = rf_model
            state["metrics"]["rf_accuracy"][ticker] = round(rf_acc, 4)

            available = [c for c in FEATURE_COLS if c in df_feat.columns] + ["close"]
            feat_array = df_feat[available].values
            lstm_model, lstm_mae = train_lstm(feat_array, ticker)
            save_lstm(lstm_model, ticker, {"mae": lstm_mae})
            _models["lstm"][ticker] = lstm_model
            state["metrics"]["lstm_mae"][ticker] = round(lstm_mae, 6)

            logger.info(f"Retrained {ticker}: RF acc={rf_acc:.3f}, LSTM mae={lstm_mae:.6f}")

        state["retrain_status"]["last_retrain"] = datetime.utcnow().isoformat()

    except Exception as e:
        logger.exception(f"Retrain error: {e}")
    finally:
        state["retrain_status"]["in_progress"] = False


def start_scheduler():
    """Start APScheduler with pipeline and retrain jobs."""
    if not scheduler.running:
        scheduler.add_job(
            run_pipeline, "interval", seconds=60,
            id="pipeline", replace_existing=True, max_instances=1,
        )
        scheduler.add_job(
            run_retrain, "cron", day_of_week="sun", hour=2, minute=0,
            id="weekly_retrain", replace_existing=True,
        )
        scheduler.start()
        logger.info("Scheduler started: pipeline every 60s, retrain every Sunday 02:00 UTC")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)