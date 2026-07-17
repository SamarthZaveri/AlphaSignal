"""
config.py — v2 universe + graph configuration.

Central place for the asset universe and edge-type toggles, so the
ablation study (design.md §4, FR7) can flip edge types on/off without
touching pipeline code.

v1's 5-asset ASSETS list in data/fetcher.py is now a subset of this
universe (kept for the v1-system baseline comparison, FR6 baseline #3).
"""
from typing import Literal
import os

# --- v1 legacy universe (kept only so v1 can still run as a baseline) ---
V1_ASSETS = ["NVDA", "MSFT", "GOOGL", "GLD", "USO"]

# --- v2 universe: 30-40 ticker, multi-sector (PRD G1 / FR1) ---
# GICS sector tagged inline so sector_edges.py doesn't need a second lookup call.
UNIVERSE: dict[str, str] = {
    # Tech
    "NVDA": "Information Technology", "MSFT": "Information Technology",
    "GOOGL": "Communication Services", "AAPL": "Information Technology",
    "META": "Communication Services", "AMD": "Information Technology",
    "AVGO": "Information Technology", "ORCL": "Information Technology",
    "CRM": "Information Technology", "ADBE": "Information Technology",
    # Financials
    "JPM": "Financials", "BAC": "Financials", "GS": "Financials",
    "MS": "Financials", "V": "Financials",
    # Healthcare
    "UNH": "Health Care", "JNJ": "Health Care", "PFE": "Health Care",
    "LLY": "Health Care", "ABBV": "Health Care",
    # Energy / Materials (macro-sensitive, overlaps v1's GLD/USO intent)
    "XOM": "Energy", "CVX": "Energy", "COP": "Energy",
    # Consumer
    "AMZN": "Consumer Discretionary", "TSLA": "Consumer Discretionary",
    "HD": "Consumer Discretionary", "MCD": "Consumer Discretionary",
    "PG": "Consumer Staples", "KO": "Consumer Staples", "WMT": "Consumer Staples",
    # Industrials
    "CAT": "Industrials", "BA": "Industrials", "GE": "Industrials",
    # Macro ETFs (retained from v1)
    "GLD": "Commodities", "USO": "Commodities",
}

TICKERS: list[str] = sorted(UNIVERSE.keys())  # 34 tickers

EdgeType = Literal["sector", "correlation", "filing_relation"]

# --- Edge-type toggles (design.md §4 graceful-degradation requirement) ---
# Read from env so the ablation runner (FR7) can flip these per-run without
# code changes: EDGE_SECTOR=0 EDGE_CORRELATION=1 EDGE_FILING_RELATION=0
def _env_flag(name: str, default: bool = True) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() not in ("0", "false", "no")


ENABLED_EDGE_TYPES: dict[EdgeType, bool] = {
    "sector": _env_flag("EDGE_SECTOR", True),
    "correlation": _env_flag("EDGE_CORRELATION", True),
    # off by default until the 10-K parser (build order step 2) exists
    "filing_relation": _env_flag("EDGE_FILING_RELATION", False),
}

# --- Correlation edge parameters (design.md §4) ---
CORRELATION_WINDOW_DAYS = 60
CORRELATION_THRESHOLD = 0.5
