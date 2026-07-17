"""
sector_edges.py — sector/GICS co-membership edges (design.md §4).

Connects any two tickers sharing a GICS sector. Static per universe —
only needs recomputing if config.UNIVERSE changes, unlike correlation
edges which are recomputed every rebalance.
"""
from itertools import combinations
from app.config import UNIVERSE


def build_sector_edges() -> list[dict]:
    """
    Returns a list of edge dicts:
      {"source": str, "target": str, "edge_type": "sector", "weight": 1.0}

    Weight is fixed at 1.0 — sector co-membership is binary, unlike
    correlation edges which carry a continuous weight.
    """
    edges = []
    by_sector: dict[str, list[str]] = {}
    for ticker, sector in UNIVERSE.items():
        by_sector.setdefault(sector, []).append(ticker)

    for sector, tickers in by_sector.items():
        for a, b in combinations(sorted(tickers), 2):
            edges.append({"source": a, "target": b, "edge_type": "sector", "weight": 1.0})

    return edges
