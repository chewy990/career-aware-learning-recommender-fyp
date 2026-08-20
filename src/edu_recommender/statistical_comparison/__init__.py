"""Public compatibility API for the statistical comparison phase."""

from .contracts import (
    AUDIT_ITEMS_PER_PATHWAY,
    BASELINE_MODELS,
    FIGURE_METADATA,
    METRICS,
    MODEL_COLOURS,
    MODEL_LABELS,
    SIGNIFICANCE_LEVEL,
    STATISTICAL_COMPARISON_VERSION,
    StatisticalComparisonResult,
)
from .findings import build_statistical_findings
from .label_audit import build_label_audit_sample
from .paired_comparison import (
    build_paired_comparison_rows,
    build_paired_difference_rows,
)
from .service import generate_statistical_comparison
from .tests import (
    effect_magnitude,
    exact_paired_permutation_test,
    exact_wilcoxon_signed_rank_test,
    holm_adjust,
)

__all__ = [
    "AUDIT_ITEMS_PER_PATHWAY",
    "BASELINE_MODELS",
    "FIGURE_METADATA",
    "METRICS",
    "MODEL_COLOURS",
    "MODEL_LABELS",
    "SIGNIFICANCE_LEVEL",
    "STATISTICAL_COMPARISON_VERSION",
    "StatisticalComparisonResult",
    "build_label_audit_sample",
    "build_paired_comparison_rows",
    "build_paired_difference_rows",
    "build_statistical_findings",
    "effect_magnitude",
    "exact_paired_permutation_test",
    "exact_wilcoxon_signed_rank_test",
    "generate_statistical_comparison",
    "holm_adjust",
]
