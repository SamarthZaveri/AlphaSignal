"""
features.py — Technical indicator computation using plain pandas.

Originally used pandas-ta, but pandas-ta pulls in numba as a hard
dependency, and numba's build explicitly refuses to install on
Python >= 3.14 (RuntimeError: "only versions >=3.10,<3.14 are
supported"). Rather than pin everyone to an older Python just for one
indicator library, RSI/MACD/Bollinger/ATR/Stochastic are implemented
directly here with pandas .rolling()/.ewm() — same formulas, zero
extra dependency, works on any Python version.
"""
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def _rsi(close: pd.Series, length: int = 14) -> pd.Series:
    """
    Relative Strength Index using Wilder's smoothing (the standard
    definition — matches TradingView/most charting platforms).
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing = an EMA with alpha = 1/length
    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    # When avg_loss is 0 (pure uptrend), RSI is 100 by definition
    rsi = rsi.where(avg_loss != 0, 100.0)
    return rsi


def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False, min_periods=length).mean()


def _macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast = _ema(close, fast)
    ema_slow = _ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def _bbands(close: pd.Series, length: int = 20, std: float = 2.0):
    """Returns (upper, mid, lower) Bollinger Bands."""
    mid = close.rolling(length, min_periods=length).mean()
    sd = close.rolling(length, min_periods=length).std(ddof=0)
    upper = mid + std * sd
    lower = mid - std * sd
    return upper, mid, lower


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    """Average True Range using Wilder's smoothing."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()


def _stoch(high: pd.Series, low: pd.Series, close: pd.Series,
           k_length: int = 14, k_smooth: int = 3, d_smooth: int = 3):
    """Returns (%K, %D) stochastic oscillator, smoothed (matches pandas-ta defaults)."""
    lowest_low = low.rolling(k_length, min_periods=k_length).min()
    highest_high = high.rolling(k_length, min_periods=k_length).max()
    raw_k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    k = raw_k.rolling(k_smooth, min_periods=k_smooth).mean()
    d = k.rolling(d_smooth, min_periods=d_smooth).mean()
    return k, d


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all technical features for a given OHLCV dataframe.
    Returns df with additional feature columns. Drops NaN rows.
    """
    if df.empty or len(df) < 50:
        logger.warning("Insufficient data for feature computation")
        return df

    df = df.copy()

    df["rsi"] = _rsi(df["close"], length=14)

    macd_line, macd_signal, macd_hist = _macd(df["close"], fast=12, slow=26, signal=9)
    df["macd"] = macd_line
    df["macd_signal"] = macd_signal
    df["macd_hist"] = macd_hist

    bb_upper, bb_mid, bb_lower = _bbands(df["close"], length=20, std=2.0)
    df["bb_upper"] = bb_upper
    df["bb_mid"] = bb_mid
    df["bb_lower"] = bb_lower
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]
    df["bb_pct"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

    df["ema_9"] = _ema(df["close"], 9)
    df["ema_21"] = _ema(df["close"], 21)
    df["ema_cross"] = (df["ema_9"] > df["ema_21"]).astype(int)

    df["volume_ma"] = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / df["volume_ma"].replace(0, 1)

    df["atr"] = _atr(df["high"], df["low"], df["close"], length=14)

    df["returns_1d"] = df["close"].pct_change(1)
    df["returns_5d"] = df["close"].pct_change(5)
    df["returns_10d"] = df["close"].pct_change(10)

    stoch_k, stoch_d = _stoch(df["high"], df["low"], df["close"])
    df["stoch_k"] = stoch_k
    df["stoch_d"] = stoch_d

    df["direction"] = (df["close"].shift(-1) > df["close"]).astype(int)

    df.dropna(inplace=True)
    return df


FEATURE_COLS = [
    "rsi", "macd", "macd_signal", "macd_hist",
    "bb_width", "bb_pct", "ema_cross",
    "volume_ratio", "atr", "returns_1d", "returns_5d", "returns_10d",
    "stoch_k", "stoch_d"
]


def get_feature_matrix(df: pd.DataFrame):
    """Extract X (features) and y (direction labels) from df."""
    available = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available].values
    y = df["direction"].values if "direction" in df.columns else np.zeros(len(df))
    return X, y


def get_latest_features(df: pd.DataFrame) -> dict:
    """Get the most recent feature snapshot as a dict."""
    if df.empty:
        return {}
    row = df.iloc[-1]
    result = {}
    for col in FEATURE_COLS:
        if col in df.columns:
            result[col] = round(float(row[col]), 4)
    result["close"] = round(float(row["close"]), 2)
    result["volume"] = int(row["volume"])
    return result