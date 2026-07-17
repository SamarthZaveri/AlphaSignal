"""
correlation_edges.py — rolling-window return-correlation edges (design.md §4).

Recomputed every rebalance (unlike sector edges, which are static).
"""
from itertools import combinations
import pandas as pd
from app.config import CORRELATION_WINDOW_DAYS, CORRELATION_THRESHOLD


def _daily_returns(price_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """price_data: ticker -> OHLCV df (as returned by fetcher.fetch_historical_universe).
    Returns a wide df of daily close-to-close returns, columns = tickers."""
    closes = {}
    for ticker, df in price_data.items():
        if df.empty or "close" not in df.columns:
            continue
        closes[ticker] = df["close"]
    wide = pd.DataFrame(closes).sort_index()
    return wide.pct_change().dropna(how="all")


def build_correlation_edges(
    price_data: dict[str, pd.DataFrame],
    window: int = CORRELATION_WINDOW_DAYS,
    threshold: float = CORRELATION_THRESHOLD,
) -> list[dict]:
    """
    Returns edge dicts: {"source", "target", "edge_type": "correlation", "weight": float}
    weight = the Pearson correlation coefficient itself (can be negative).
    Only edges with |correlation| > threshold over the trailing `window`
    trading days are kept.
    """
    returns = _daily_returns(price_data)
    if returns.empty or len(returns) < window:
        # Not enough history yet — return no edges rather than a noisy
        # correlation matrix on too few observations.
        return []

    windowed = returns.tail(window)
    corr = windowed.corr(min_periods=max(10, window // 2))

    edges = []
    tickers = list(corr.columns)
    for a, b in combinations(sorted(tickers), 2):
        if a not in corr.index or b not in corr.columns:
            continue
        rho = corr.loc[a, b]
        if pd.isna(rho) or abs(rho) <= threshold:
            continue
        edges.append({"source": a, "target": b, "edge_type": "correlation", "weight": float(rho)})

    return edges
