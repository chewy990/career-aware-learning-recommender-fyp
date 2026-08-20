"""Public compatibility API for the prerequisite experiment phase."""

from .contracts import (
    BASELINE_MODEL,
    FIGURE_METADATA,
    MODEL_COLOURS,
    MODEL_LABELS,
    PLANNED_METRICS,
    PREREQUISITE_EXPERIMENT_VERSION,
    PRIMARY_K,
    SIGNIFICANCE_LEVEL,
    VARIANT_MODEL,
    PrerequisiteExperimentResult,
)
from .eligibility import build_eligible_recommendations
from .findings import build_findings
from .paired_comparison import build_paired_rows
from .profile_changes import build_profile_change_rows
from .service import generate_prerequisite_experiment
from .targeted_audit import build_targeted_audit

__all__ = [
    "BASELINE_MODEL",
    "FIGURE_METADATA",
    "MODEL_COLOURS",
    "MODEL_LABELS",
    "PLANNED_METRICS",
    "PREREQUISITE_EXPERIMENT_VERSION",
    "PRIMARY_K",
    "SIGNIFICANCE_LEVEL",
    "VARIANT_MODEL",
    "PrerequisiteExperimentResult",
    "build_eligible_recommendations",
    "build_findings",
    "build_paired_rows",
    "build_profile_change_rows",
    "build_targeted_audit",
    "generate_prerequisite_experiment",
]
