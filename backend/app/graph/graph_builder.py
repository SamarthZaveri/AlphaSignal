"""
graph_builder.py — assembles the multi-relational graph for a rebalance date.

Graceful-degradation requirement (design.md §4, PRD Risk #1): no code
path here assumes all three edge types are present. Each edge type is
gated by config.ENABLED_EDGE_TYPES, so the ablation study (FR7) can run
sector-only / correlation-only / filing-relation-only / all-combined
just by changing config/env, with zero code changes.

filing_relation edges are stubbed until the 10-K parser (build order
step 2) exists — enabling that flag before then raises clearly rather
than silently returning nothing.
"""
import logging
from app.config import UNIVERSE, ENABLED_EDGE_TYPES
from app.graph.sector_edges import build_sector_edges
from app.graph.correlation_edges import build_correlation_edges

logger = logging.getLogger(__name__)


def build_graph(price_data: dict, rebalance_date: str | None = None) -> dict:
    """
    Returns:
      {
        "date": str | None,
        "nodes": [{"ticker": str, "sector": str}, ...],
        "edges": [{"source", "target", "edge_type", "weight"}, ...],
        "edge_types_used": [str, ...],   # for logging / ablation report tagging
      }

    This is a plain-dict graph object for now (step 1). It gets converted
    to a torch_geometric HeteroData object in the GNN module (build order
    step 3, design.md §3.1) — kept out of this step so step 1 has no
    torch/torch_geometric dependency yet.
    """
    nodes = [{"ticker": t, "sector": s} for t, s in UNIVERSE.items()]
    edges: list[dict] = []
    used: list[str] = []

    if ENABLED_EDGE_TYPES.get("sector"):
        sector_edges = build_sector_edges()
        edges.extend(sector_edges)
        used.append("sector")
        logger.info(f"graph_builder: {len(sector_edges)} sector edges")

    if ENABLED_EDGE_TYPES.get("correlation"):
        corr_edges = build_correlation_edges(price_data)
        edges.extend(corr_edges)
        used.append("correlation")
        logger.info(f"graph_builder: {len(corr_edges)} correlation edges")

    if ENABLED_EDGE_TYPES.get("filing_relation"):
        raise NotImplementedError(
            "filing_relation edges require the 10-K parser (build order step 2, "
            "app/filings/relation_extraction.py), which doesn't exist yet. "
            "Set EDGE_FILING_RELATION=0 to run without it."
        )

    if not used:
        logger.warning("graph_builder: no edge types enabled — graph has isolated nodes only")

    return {
        "date": rebalance_date,
        "nodes": nodes,
        "edges": edges,
        "edge_types_used": used,
    }
