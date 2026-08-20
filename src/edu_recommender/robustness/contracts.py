"""Own robustness contracts responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from dataclasses import dataclass

from edu_recommender.models import (
    HYBRID_WEIGHTS,
)

ROBUSTNESS_VERSION = 1

SENSITIVITY_MULTIPLIERS = (0.5, 0.75, 1.0, 1.25, 1.5)

SEEDED_CONFIGURATION_COUNT = 12

SEEDED_MULTIPLIER_RANGE = (0.75, 1.25)

FAILURE_THRESHOLDS = {
    "low_ndcg_at_5": 0.80,
    "low_recall_at_5": 0.15,
    "weak_skill_gap_coverage_at_5": 0.50,
    "provider_concentration_at_5": 0.60,
    "format_concentration_at_5": 0.80,
}

COMPONENTS = tuple(HYBRID_WEIGHTS)

MODEL_COLOUR = "#7C3AED"

POSITIVE_COLOUR = "#22C55E"

NEGATIVE_COLOUR = "#DC2626"

NEUTRAL_COLOUR = "#A3A3A3"

FIGURE_METADATA = {"Software": "Career-Aware Recommender Phase 4"}

@dataclass(frozen=True)
class RobustnessResult:
    """Record robustness tables, findings, and generated artifact paths."""

    ablation_summary_rows: tuple[dict[str, object], ...]
    ablation_profile_rows: tuple[dict[str, object], ...]
    sensitivity_rows: tuple[dict[str, object], ...]
    seeded_configuration_rows: tuple[dict[str, object], ...]
    seeded_result_rows: tuple[dict[str, object], ...]
    contribution_rows: tuple[dict[str, object], ...]
    failure_rows: tuple[dict[str, object], ...]
    findings: tuple[dict[str, str], ...]
    output_files: tuple[str, ...]
