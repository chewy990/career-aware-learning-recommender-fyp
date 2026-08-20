"""Own statistical comparison contracts responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from dataclasses import dataclass

STATISTICAL_COMPARISON_VERSION = 1

BASELINE_MODELS = ("popularity", "content_based")

METRICS = ("precision_at_k", "recall_at_k", "ndcg_at_k")

SIGNIFICANCE_LEVEL = 0.05

AUDIT_ITEMS_PER_PATHWAY = 8

MODEL_LABELS = {
    "popularity": "Popularity",
    "content_based": "Content-based",
    "hybrid": "Hybrid",
}

MODEL_COLOURS = {
    "popularity": "#A3A3A3",
    "content_based": "#C4B5FD",
    "hybrid": "#7C3AED",
}

FIGURE_METADATA = {"Software": "Career-Aware Recommender Phase 5"}

@dataclass(frozen=True)
class StatisticalComparisonResult:
    """Record paired statistical tests, adjusted results, and artifacts."""

    difference_rows: tuple[dict[str, object], ...]
    comparison_rows: tuple[dict[str, object], ...]
    audit_blinded_rows: tuple[dict[str, object], ...]
    audit_key_rows: tuple[dict[str, object], ...]
    findings: tuple[dict[str, str], ...]
    output_files: tuple[str, ...]
