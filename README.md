# AlphaSignal

A deployed research dashboard that runs four ML models on five assets in
real time, fuses their signals into a paper-trading agent that reasons out
loud, and displays honest results against a buy-and-hold baseline. One URL.
No login. Updates every minute.

```
Price/Volume → Random Forest → LSTM → VADER Sentiment → PPO Agent → Trade + Reason
```

Each model's output feeds the next. PPO is the only model that *acts* — the
other three are signal generators. Every trade gets a plain-English reason
logged alongside it.

## Why this is different

Most student ML-trading projects do **one** of: classical ML, deep
learning, NLP, or RL. AlphaSignal runs all four in a single sequential
inference pipeline, and every trade comes with a human-readable
explanation — the kind of line an analyst would actually write:

> *LSTM projects 1.80% upside (target close: $941.20). RF signals UP
> momentum with 72% probability (RSI 58, MACD crossover). Volume 1.8x above
> average — strong conviction. News sentiment STRONGLY POSITIVE (+0.65).
> RL policy confirms BUY (confidence: 81%).*

That reasoning column is what gets screenshotted.

## Live demo

`https://alphasignal-frontend.onrender.com` _(update after deploy)_

## Architecture

| Layer | Tool |
|---|---|
| Data | yfinance + NewsAPI free tier |
| Features | pandas-ta (RSI, MACD, Bollinger, ATR, stochastic) |
| Classical ML | scikit-learn RandomForestClassifier (direction probability) |
| Deep learning | PyTorch LSTM (predicted close price) |
| NLP | NLTK VADER (headline sentiment, −1 to 1) |
| RL | Stable-Baselines3 PPO + Gymnasium (BUY/HOLD/SELL) |
| Scheduler | APScheduler inside FastAPI (60s pipeline, weekly retrain) |
| Backend | FastAPI + WebSocket |
| Frontend | React + Recharts + custom dark-terminal UI |
| Storage | Flat CSV (`trades.csv`) — zero infra, fully downloadable |
| Deployment | Render (Docker backend + static frontend) |

## Asset universe

NVDA, MSFT, GOOGL (correlated tech, high news volume), GLD (gold ETF — macro
sensitivity), USO (oil ETF — macro sensitivity). All five trade on yfinance
with no special data vendor required.

## Running locally

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add NEWSAPI_KEY if you have one — optional, falls back to mock sentiment
uvicorn app.main:app --reload --port 8000
```

The server starts the 60-second pipeline immediately on boot and exposes:

- `GET /health` — liveness + last pipeline run timestamp
- `GET /signals` / `GET /signals/{ticker}` — latest fused model output
- `GET /portfolio` — paper-trading P&L, Sharpe, alpha vs. SPY
- `GET /trades` / `GET /trades/download` — full trade history as CSV
- `GET /models/status` / `GET /models/feature-importance` — model lifecycle
- `POST /models/retrain` — trigger retraining on demand
- `WS /ws` — live signal + portfolio push every 60s

Interactive API docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # point REACT_APP_API_URL at your backend
npm start
```

Three pages: **Live** (per-asset price + all four model outputs + sentiment
feed), **Trades** (full reasoning log, P&L vs. SPY, CSV export), **Models**
(accuracy, Sharpe, feature importance, retrain controls).

### Training models before first deploy

Run `notebooks/train_offline.ipynb` to populate `backend/checkpoints/`
with trained RF, LSTM, and PPO weights. Without checkpoints, the pipeline
runs on a transparent heuristic fallback (clearly labeled `"source":
"heuristic"` in API responses) so the dashboard never silently fakes a
trained-model result.

## Deployment

Render configs are included for both services (`backend/render.yaml`,
`frontend/render.yaml`). Push to `main` and GitHub Actions
(`.github/workflows/deploy.yml`) lints, runs a sanity import test, builds
the frontend, and triggers Render deploy hooks.

## Honest results

See [`RESULTS.md`](./RESULTS.md) for real accuracy numbers, Sharpe vs. SPY,
what failed, and what I'd change. Numbers populate after the first
training cycle — this isn't a project that claims results before it has
run.

## Scope boundaries

**In:** 5 assets, paper trading, 1-minute poll, all 4 models, reasoning
log, CSV export, public deploy, SPY baseline, walk-forward CV, weekly
retrain cron.

**Out:** real money, order book data, options, user accounts, a database
(flat CSV only — by design), multiple strategies, hyperparameter tuning UI.

---

Paper trading only. Not financial advice.
