"""
fetcher.py — yfinance poll for all 5 assets every 60 seconds.
Returns clean OHLCV dataframes with timestamps.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

ASSETS = ["NVDA", "MSFT", "GOOGL", "GLD", "USO"]  # v1 — kept for the v1-baseline comparison (FR6)


def fetch_latest(ticker: str, period: str = "5d", interval: str = "1m") -> pd.DataFrame:
    """Fetch OHLCV data for a single ticker."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period=period, interval=interval)
        if df.empty:
            logger.warning(f"Empty dataframe for {ticker}")
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = ["open", "high", "low", "close", "volume"]
        df["ticker"] = ticker
        df.dropna(inplace=True)
        return df
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()


def fetch_historical(ticker: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """Fetch historical daily data for model training."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = ["open", "high", "low", "close", "volume"]
        df["ticker"] = ticker
        df.dropna(inplace=True)
        return df
    except Exception as e:
        logger.error(f"Error fetching historical {ticker}: {e}")
        return pd.DataFrame()


def fetch_all_latest() -> dict:
    """Fetch latest data for all 5 assets. Returns dict ticker -> df."""
    results = {}
    for ticker in ASSETS:
        df = fetch_latest(ticker)
        if not df.empty:
            results[ticker] = df
            logger.info(f"Fetched {len(df)} rows for {ticker}, latest close: {df['close'].iloc[-1]:.2f}")
    return results


def fetch_all_historical() -> dict:
    """Fetch 2 years of daily data for all assets. Used for training."""
    results = {}
    for ticker in ASSETS:
        df = fetch_historical(ticker)
        if not df.empty:
            results[ticker] = df
            logger.info(f"Historical: {len(df)} days for {ticker}")
    return results


def fetch_historical_universe(period: str = "2y", interval: str = "1d") -> dict:
    """
    v2: fetch historical daily data for the full config.TICKERS universe
    (30-40 tickers), not just the v1 5-asset ASSETS list.

    Reuses fetch_historical per-ticker so caching/error-handling stays in
    one place; graph_builder.py and correlation_edges.py consume this.
    """
    from app.config import TICKERS

    results = {}
    for ticker in TICKERS:
        df = fetch_historical(ticker, period=period, interval=interval)
        if not df.empty:
            results[ticker] = df
            logger.info(f"[v2 universe] {len(df)} days for {ticker}")
        else:
            logger.warning(f"[v2 universe] no data for {ticker} — will be dropped from graph")
    return results


def get_current_prices() -> dict:
    """Quick snapshot of current prices."""
    prices = {}
    for ticker in ASSETS:
        try:
            tk = yf.Ticker(ticker)
            info = tk.fast_info
            prices[ticker] = round(float(info.last_price), 2)
        except Exception as e:
            logger.error(f"Price fetch error for {ticker}: {e}")
            prices[ticker] = 0.0
    return prices
