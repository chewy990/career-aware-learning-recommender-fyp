"""Own statistical comparison service responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

from edu_recommender.data import LearnerProfile, Resource, write_rows
from edu_recommender.evaluation import (
    DEFAULT_BOOTSTRAP_REPLICATES,
    EvaluationResult,
)
from edu_recommender.models import Recommendation

from .contracts import StatisticalComparisonResult
from .findings import build_statistical_findings
from .label_audit import build_label_audit_sample
from .paired_comparison import (
    build_paired_comparison_rows,
    build_paired_difference_rows,
)
from .reporting import _write_summary


def generate_statistical_comparison(
    evaluation_result: EvaluationResult,
    recommendations_by_model: dict[str, dict[str, list[Recommendation]]],
    profiles: list[LearnerProfile],
    resources: list[Resource],
    relevance_judgements: dict[str, set[str]],
    output_dir: Path,
    random_seed: int,
    bootstrap_replicates: int = DEFAULT_BOOTSTRAP_REPLICATES,
) -> StatisticalComparisonResult:
    """Run paired statistical comparisons and write the phase's owned artifacts."""

    difference_rows = build_paired_difference_rows(
        evaluation_result.profile_rows
    )
    comparison_rows = build_paired_comparison_rows(
        difference_rows,
        random_seed=random_seed,
        bootstrap_replicates=bootstrap_replicates,
    )
    audit_blinded_rows, audit_key_rows = build_label_audit_sample(
        recommendations_by_model["hybrid"],
        profiles,
        resources,
        relevance_judgements,
        random_seed=random_seed,
    )
    findings = build_statistical_findings(
        comparison_rows,
        audit_key_rows,
    )

    table_specs = {
        "phase5_profile_differences.csv": (
            [
                "comparison",
                "baseline_model",
                "metric",
                "k",
                "profile_id",
                "pathway",
                "hybrid_value",
                "baseline_value",
                "paired_difference",
            ],
            difference_rows,
        ),
        "phase5_paired_comparisons.csv": (
            [
                "comparison",
                "baseline_model",
                "metric",
                "k",
                "profile_count",
                "mean_difference",
                "median_difference",
                "sample_stddev_difference",
                "ci_95_lower",
                "ci_95_upper",
                "standardized_effect_dz",
                "effect_magnitude",
                "hybrid_wins",
                "ties",
                "hybrid_losses",
                "exact_permutation_p",
                "exact_permutation_holm_p",
                "wilcoxon_w_plus",
                "wilcoxon_p",
                "wilcoxon_holm_p",
                "holm_significant_at_0_05",
                "bootstrap_replicates",
                "random_seed",
            ],
            comparison_rows,
        ),
        "relevance_audit_blinded.csv": (
            [
                "audit_item_id",
                "pathway",
                "profile_name",
                "target_pathway",
                "current_skills",
                "weak_skills",
                "preferred_difficulty",
                "resource_title",
                "provider",
                "topic",
                "skills",
                "resource_difficulty",
                "format",
                "prerequisites",
                "reviewer_relevance",
                "reviewer_confidence",
                "reviewer_notes",
            ],
            audit_blinded_rows,
        ),
        "relevance_audit_key.csv": (
            [
                "audit_item_id",
                "profile_id",
                "resource_id",
                "current_label",
                "selection_reason",
            ],
            audit_key_rows,
        ),
        "phase5_findings.csv": (
            ["title", "finding", "implication"],
            list(findings),
        ),
    }
    for filename, (fieldnames, rows) in table_specs.items():
        write_rows(output_dir / filename, fieldnames, rows)

    from .figures import _write_figures

    figure_files = _write_figures(
        difference_rows,
        comparison_rows,
        output_dir,
    )
    _write_summary(findings, figure_files, output_dir)
    output_files = (
            *table_specs,
            "phase5_summary.md",
            *figure_files,
        )
    return StatisticalComparisonResult(
        difference_rows=tuple(difference_rows),
        comparison_rows=tuple(comparison_rows),
        audit_blinded_rows=tuple(audit_blinded_rows),
        audit_key_rows=tuple(audit_key_rows),
        findings=findings,
        output_files=output_files,
    )
