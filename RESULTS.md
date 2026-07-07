# AlphaSignal — Results

> Honest numbers from the running system. This file is regenerated after each
> live trading session; the version below is from the initial deployment
> checkpoint before the first weekly retrain.

## Status at time of writing

The system is live but has not yet completed its first weekly retrain cycle,
so model checkpoints are running on the **heuristic fallback** described in
`rl_agent.py` rather than a trained PPO policy. Random Forest and LSTM
checkpoints are trained offline via `notebooks/train_offline.ipynb` before
first deploy — re-run that notebook and redeploy to populate the numbers
below with real trained-model results.

## Directional accuracy (Random Forest, 5-fold time-series CV)

| Asset | RF Accuracy | vs. Random Baseline (50%) |
|---|---|---|
| NVDA  | _pending first retrain_ | — |
| MSFT  | _pending first retrain_ | — |
| GOOGL | _pending first retrain_ | — |
| GLD   | _pending first retrain_ | — |
| USO   | _pending first retrain_ | — |

Fill in after running `notebooks/train_offline.ipynb` or after the first
Sunday 02:00 UTC retrain cron fires. Time-series cross-validation means no
lookahead bias — each fold trains only on data strictly before its
validation window.

## LSTM validation loss

LSTM is trained with a Huber loss on normalized next-period returns, not
raw price, to avoid the model trivially learning "predict yesterday's
price." Validation loss (best checkpoint, post early-stop):

| Asset | Val Loss (Huber) |
|---|---|
| NVDA  | _pending first retrain_ |
| MSFT  | _pending first retrain_ |
| GOOGL | _pending first retrain_ |
| GLD   | _pending first retrain_ |
| USO   | _pending first retrain_ |

## RF feature importances (one sentence each)

Populated from `/models/feature-importance` after the first retrain. In
backtesting on similar setups, RSI, MACD histogram, and volume ratio
typically dominate for momentum names (NVDA, MSFT, GOOGL), while GLD and
USO lean more on ATR and Bollinger %B — consistent with macro assets
trading on volatility regime rather than momentum.

## PPO vs. buy-and-hold Sharpe

| Strategy | Sharpe (annualized) | Cumulative Return |
|---|---|---|
| AlphaSignal (PPO fusion) | _pending live trading days_ | _pending_ |
| SPY buy-and-hold | _pending_ | _pending_ |

Sharpe is computed from daily paper-trading returns,
`mean(daily_return) / std(daily_return) * sqrt(252)`. A Sharpe above 1.0 is
considered good for a research strategy; above 2.0 is excellent. Live values
populate at `/portfolio` and the Models tab once trades accumulate across
multiple sessions — a single day of data is not enough to trust a Sharpe
estimate, so treat early numbers as illustrative only.

## What failed / known limitations

- **Sentiment lag.** VADER scores headlines as they're fetched, but news
  that moves markets is often priced in within minutes — by the time the
  60-second pipeline polls NewsAPI, some signal value has already decayed.
- **Small-sample overfitting risk.** Daily-bar training windows (2 years
  ≈ 500 rows) are thin for a 200k-step PPO policy; the policy can latch
  onto spurious correlations specific to the training period. Walk-forward
  CV on RF/LSTM mitigates this for the supervised models, but PPO's reward
  shaping is more exposed to regime shift.
- **No transaction cost modeling beyond a flat penalty.** Real slippage and
  bid-ask spread on 1-minute bars would erode paper-trading P&L further,
  especially on GLD/USO where spreads are wider than NVDA/MSFT/GOOGL.
- **NewsAPI free tier rate limits.** Mock sentiment data kicks in
  automatically when no `NEWSAPI_KEY` is set or the quota is exhausted —
  this is clearly labeled in the reasoning log via deterministic synthetic
  headlines, never silently substituted as real data.
- **Single-asset PPO training.** The shipped PPO checkpoint is trained
  on NVDA's price series only (see `train_offline.ipynb`); it generalizes
  to other tickers via the shared 6-dim observation space, but per-asset
  PPO fine-tuning would likely improve results for GLD/USO given their
  different volatility regime.

## What I'd change next

- Train a separate PPO policy per asset (or per asset class: tech vs.
  macro) instead of one shared policy, given the regime differences noted
  above.
- Swap VADER for FinBERT (already scoped as a bonus in the PRD) — VADER's
  general-purpose lexicon misreads financial-domain phrasing more often
  than a model fine-tuned on financial text.
- Add a transaction-cost-aware reward term to the Gym environment that
  scales with `volume_ratio`, since real slippage is volume-dependent and
  the current flat `-0.1` penalty per trade doesn't capture that.
- Track maximum drawdown explicitly in `portfolio.py` (currently approximated
  in the frontend) so the Models tab can show a real number instead of an
  estimate.
