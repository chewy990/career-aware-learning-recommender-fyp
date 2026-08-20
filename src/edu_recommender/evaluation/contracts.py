"""Own evaluation contracts responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from dataclasses import dataclass

EVALUATION_VERSION = 2

DEFAULT_K_VALUES = (3, 5, 10)

DEFAULT_BOOTSTRAP_REPLICATES = 10_000

METRIC_NAMES = ("precision_at_k", "recall_at_k", "ndcg_at_k")

MODEL_ORDER = ("popularity", "content_based", "hybrid")

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

FIGURE_METADATA = {"Software": "Career-Aware Recommender Phase 3"}

@dataclass(frozen=True)
class EvaluationResult:
    """Record evaluation tables, findings, and generated artifact paths."""

    summary_rows: tuple[dict[str, object], ...]
    profile_rows: tuple[dict[str, object], ...]
    pathway_rows: tuple[dict[str, object], ...]
    uncertainty_rows: tuple[dict[str, object], ...]
    diagnostic_profile_rows: tuple[dict[str, object], ...]
    diagnostic_summary_rows: tuple[dict[str, object], ...]
    findings: tuple[dict[str, str], ...]
    output_files: tuple[str, ...]
