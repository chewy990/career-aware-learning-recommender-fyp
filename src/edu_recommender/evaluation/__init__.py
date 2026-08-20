"""Public compatibility API for the evaluation phase."""

from .contracts import (
    DEFAULT_BOOTSTRAP_REPLICATES,
    DEFAULT_K_VALUES,
    EVALUATION_VERSION,
    FIGURE_METADATA,
    METRIC_NAMES,
    MODEL_COLOURS,
    MODEL_LABELS,
    MODEL_ORDER,
    EvaluationResult,
)
from .diagnostics import (
    build_diagnostic_profile_rows,
    build_diagnostic_summary_rows,
    difficulty_match_rate,
    intra_list_diversity,
    prerequisite_validity_rate,
    skill_gap_coverage,
)
from .findings import build_evaluation_findings
from .metrics import (
    build_metric_summary_rows,
    build_pathway_metric_rows,
    build_profile_metric_rows,
    evaluate_recommendations,
)
from .ranking_metrics import ndcg_at_k, precision_at_k, recall_at_k
from .service import generate_evaluation
from .uncertainty import bootstrap_mean_confidence_interval, build_uncertainty_rows

__all__ = [
    "DEFAULT_BOOTSTRAP_REPLICATES",
    "DEFAULT_K_VALUES",
    "EVALUATION_VERSION",
    "FIGURE_METADATA",
    "METRIC_NAMES",
    "MODEL_COLOURS",
    "MODEL_LABELS",
    "MODEL_ORDER",
    "EvaluationResult",
    "bootstrap_mean_confidence_interval",
    "build_diagnostic_profile_rows",
    "build_diagnostic_summary_rows",
    "build_evaluation_findings",
    "build_metric_summary_rows",
    "build_pathway_metric_rows",
    "build_profile_metric_rows",
    "build_uncertainty_rows",
    "difficulty_match_rate",
    "evaluate_recommendations",
    "generate_evaluation",
    "intra_list_diversity",
    "ndcg_at_k",
    "precision_at_k",
    "prerequisite_validity_rate",
    "recall_at_k",
    "skill_gap_coverage",
]
