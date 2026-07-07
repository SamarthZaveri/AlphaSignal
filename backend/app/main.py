"""
main.py — FastAPI application with REST endpoints, WebSocket, and scheduler.
"""
import os
import json
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy scalar types (float32, int64, etc.)"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def safe_json_dumps(data: dict) -> str:
    return json.dumps(data, cls=NumpyEncoder)


class ConnectionManager:
    def __init__(self):
        self.active = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info(f"WS connected. Total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        logger.info(f"WS disconnected. Total: {len(self.active)}")

    async def broadcast(self, data: dict):
        payload = safe_json_dumps(data)
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.scheduler import load_models, start_scheduler, set_broadcast, run_pipeline

    logger.info("AlphaSignal backend starting up...")
    load_models()
    set_broadcast(manager.broadcast)
    start_scheduler()

    asyncio.create_task(run_pipeline())
    logger.info("Initial pipeline triggered.")

    yield

    from app.scheduler import stop_scheduler
    stop_scheduler()
    logger.info("Scheduler stopped.")


app = FastAPI(
    title="AlphaSignal API",
    description="4-model sequential ML trading pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    from app.scheduler import state
    return {
        "status": "ok",
        "models_loaded": state["models_loaded"],
        "last_pipeline_run": state["last_run"],
        "active_ws_connections": len(manager.active),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/metrics")
async def metrics():
    from app.scheduler import state
    from app.portfolio import get_portfolio
    portfolio = get_portfolio()
    prices = state.get("current_prices", {})
    return {
        "rf_accuracy": state["metrics"]["rf_accuracy"],
        "lstm_mae": state["metrics"]["lstm_mae"],
        "portfolio": portfolio.summary(prices) if prices else {},
        "retrain_status": state["retrain_status"],
    }


@app.get("/signals")
async def get_signals():
    from app.scheduler import state
    return {
        "signals": state["last_signals"],
        "prices": state["current_prices"],
        "timestamp": state["last_run"],
    }


@app.get("/signals/{ticker}")
async def get_ticker_signal(ticker: str):
    from app.scheduler import state
    from app.data.fetcher import ASSETS
    ticker = ticker.upper()
    if ticker not in ASSETS:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    signal = state["last_signals"].get(ticker)
    if not signal:
        raise HTTPException(status_code=503, detail="Pipeline not yet run")
    return signal


@app.get("/portfolio")
async def get_portfolio_summary():
    from app.portfolio import get_portfolio
    from app.scheduler import state
    portfolio = get_portfolio()
    prices = state.get("current_prices", {})
    return portfolio.summary(prices)


@app.get("/sentiment")
async def get_sentiment():
    from app.scheduler import state
    return state.get("sentiment_cache", {})


@app.get("/trades")
async def get_trades(limit: int = 100, ticker: Optional[str] = None):
    from app.logger import get_all_trades
    trades = get_all_trades()
    if ticker:
        trades = [t for t in trades if t.get("ticker", "").upper() == ticker.upper()]
    return {"trades": trades[-limit:], "total": len(trades)}


@app.get("/trades/download")
async def download_trades():
    from app.logger import get_trades_path
    path = get_trades_path()
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No trades recorded yet")
    return FileResponse(
        path, media_type="text/csv",
        filename=f"alphasignal_trades_{datetime.utcnow().strftime('%Y%m%d')}.csv",
    )


@app.get("/models/status")
async def models_status():
    from app.scheduler import _models, state
    return {
        "rf": {ticker: (m is not None) for ticker, m in _models["rf"].items()},
        "lstm": {ticker: (m is not None) for ticker, m in _models["lstm"].items()},
        "ppo": _models["ppo"] is not None,
        "metrics": state["metrics"],
        "retrain": state["retrain_status"],
    }


@app.post("/models/retrain")
async def trigger_retrain():
    from app.scheduler import run_retrain, state
    if state["retrain_status"]["in_progress"]:
        return {"status": "already_running"}
    asyncio.create_task(run_retrain())
    return {"status": "triggered", "timestamp": datetime.utcnow().isoformat()}


@app.get("/models/feature-importance")
async def feature_importance():
    from app.scheduler import _models
    from app.models.random_forest import get_feature_importances
    from app.data.features import FEATURE_COLS
    result = {}
    for ticker, model in _models["rf"].items():
        if model is not None:
            result[ticker] = get_feature_importances(model, FEATURE_COLS)
    return result


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        from app.scheduler import state
        from app.portfolio import get_portfolio
        portfolio = get_portfolio()
        prices = state.get("current_prices", {})
        await websocket.send_text(safe_json_dumps({
            "type": "init",
            "signals": state["last_signals"],
            "portfolio": portfolio.summary(prices) if prices else {},
            "timestamp": state["last_run"],
        }))

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(safe_json_dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                await websocket.send_text(safe_json_dumps({"type": "heartbeat",
                                                       "timestamp": datetime.utcnow().isoformat()}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)