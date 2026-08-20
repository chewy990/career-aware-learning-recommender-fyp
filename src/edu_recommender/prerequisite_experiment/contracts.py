"""Own prerequisite experiment contracts responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from dataclasses import dataclass

from edu_recommender.models import (
    Recommendation,
)

PREREQUISITE_EXPERIMENT_VERSION = 1

BASELINE_MODEL = "hybrid"

VARIANT_MODEL = "hybrid_hard_prerequisites"

PRIMARY_K = 5

PLANNED_METRICS = ("precision_at_k", "recall_at_k", "ndcg_at_k")

SIGNIFICANCE_LEVEL = 0.05

MODEL_LABELS = {
    BASELINE_MODEL: "Hybrid baseline",
    VARIANT_MODEL: "Hard-prerequisite hybrid",
}

MODEL_COLOURS = {
    BASELINE_MODEL: "#A3A3A3",
    VARIANT_MODEL: "#7C3AED",
}

FIGURE_METADATA = {
    "Software": "Career-Aware Recommender Prerequisite Experiment"
}

@dataclass(frozen=True)
class PrerequisiteExperimentResult:
    """Record paired prerequisite experiment outputs and artifact paths."""

    variant_recommendations: dict[str, list[Recommendation]]
    profile_metric_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    pathway_rows: tuple[dict[str, object], ...]
    paired_rows: tuple[dict[str, object], ...]
    diagnostic_rows: tuple[dict[str, object], ...]
    profile_change_rows: tuple[dict[str, object], ...]
    audit_blinded_rows: tuple[dict[str, object], ...]
    audit_key_rows: tuple[dict[str, object], ...]
    findings: tuple[dict[str, str], ...]
    output_files: tuple[str, ...]
