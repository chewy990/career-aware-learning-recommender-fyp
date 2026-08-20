"""Own evaluation service responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

from edu_recommender.data import LearnerProfile, Resource, write_rows
from edu_recommender.models import Recommendation

from .contracts import DEFAULT_BOOTSTRAP_REPLICATES, DEFAULT_K_VALUES, EvaluationResult
from .diagnostics import build_diagnostic_profile_rows, build_diagnostic_summary_rows
from .findings import build_evaluation_findings
from .metrics import (
    build_metric_summary_rows,
    build_pathway_metric_rows,
    build_profile_metric_rows,
)
from .reporting import _validate_k_values, _write_evaluation_summary
from .uncertainty import build_uncertainty_rows


def generate_evaluation(
    recommendations_by_model: dict[str, dict[str, list[Recommendation]]],
    relevance_judgements: dict[str, set[str]],
    profiles: list[LearnerProfile],
    resources: list[Resource],
    skill_gaps_by_profile: dict[str, dict[str, float]],
    output_dir: Path,
    k_values: tuple[int, ...] = DEFAULT_K_VALUES,
    random_seed: int = 42,
    bootstrap_replicates: int = DEFAULT_BOOTSTRAP_REPLICATES,
) -> EvaluationResult:
    """Run evaluation orchestration and write only the evaluation phase's artifacts."""

    _validate_k_values(k_values)
    profile_rows = build_profile_metric_rows(
        recommendations_by_model,
        relevance_judgements,
        profiles,
        k_values,
    )
    summary_rows = build_metric_summary_rows(profile_rows)
    pathway_rows = build_pathway_metric_rows(profile_rows)
    uncertainty_rows = build_uncertainty_rows(
        profile_rows,
        random_seed,
        bootstrap_replicates,
    )
    diagnostic_profile_rows = build_diagnostic_profile_rows(
        recommendations_by_model,
        profiles,
        resources,
        skill_gaps_by_profile,
        k_values,
    )
    diagnostic_summary_rows = build_diagnostic_summary_rows(
        diagnostic_profile_rows,
        recommendations_by_model,
        resources,
        k_values,
    )
    findings = build_evaluation_findings(
        summary_rows,
        pathway_rows,
        uncertainty_rows,
        diagnostic_summary_rows,
    )

    table_specs = {
        "evaluation_metrics.csv": (
            [
                "model",
                "k",
                "profile_count",
                "precision_at_k",
                "recall_at_k",
                "ndcg_at_k",
            ],
            summary_rows,
        ),
        "evaluation_profile_metrics.csv": (
            [
                "model",
                "profile_id",
                "pathway",
                "k",
                "recommended_count",
                "relevant_count",
                "relevant_hits",
                "precision_at_k",
                "recall_at_k",
                "ndcg_at_k",
            ],
            profile_rows,
        ),
        "evaluation_pathway_metrics.csv": (
            [
                "model",
                "pathway",
                "k",
                "profile_count",
                "precision_at_k",
                "recall_at_k",
                "ndcg_at_k",
            ],
            pathway_rows,
        ),
        "evaluation_uncertainty.csv": (
            [
                "model",
                "k",
                "metric",
                "profile_count",
                "mean",
                "median",
                "sample_stddev",
                "ci_95_lower",
                "ci_95_upper",
                "bootstrap_replicates",
                "random_seed",
            ],
            uncertainty_rows,
        ),
        "recommendation_diagnostics_profile.csv": (
            [
                "model",
                "profile_id",
                "pathway",
                "k",
                "recommended_count",
                "distinct_provider_count",
                "provider_diversity",
                "distinct_format_count",
                "format_diversity",
                "skill_gap_coverage",
                "intra_list_diversity",
                "difficulty_match_rate",
                "prerequisite_validity_rate",
            ],
            diagnostic_profile_rows,
        ),
        "recommendation_diagnostics_summary.csv": (
            [
                "model",
                "k",
                "profile_count",
                "unique_resources_recommended",
                "catalogue_size",
                "catalogue_coverage",
                "provider_exposure_count",
                "format_exposure_count",
                "provider_diversity",
                "format_diversity",
                "skill_gap_coverage",
                "intra_list_diversity",
                "difficulty_match_rate",
                "prerequisite_validity_rate",
            ],
            diagnostic_summary_rows,
        ),
        "phase3_findings.csv": (
            ["title", "finding", "implication"],
            list(findings),
        ),
    }
    for filename, (fieldnames, rows) in table_specs.items():
        write_rows(output_dir / filename, fieldnames, rows)

    from .figures import _write_evaluation_figures

    figure_files = _write_evaluation_figures(
        summary_rows,
        profile_rows,
        pathway_rows,
        uncertainty_rows,
        diagnostic_summary_rows,
        output_dir,
    )
    _write_evaluation_summary(findings, figure_files, output_dir)
    output_files = (
            *table_specs,
            "phase3_summary.md",
            *figure_files,
        )
    return EvaluationResult(
        summary_rows=tuple(summary_rows),
        profile_rows=tuple(profile_rows),
        pathway_rows=tuple(pathway_rows),
        uncertainty_rows=tuple(uncertainty_rows),
        diagnostic_profile_rows=tuple(diagnostic_profile_rows),
        diagnostic_summary_rows=tuple(diagnostic_summary_rows),
        findings=findings,
        output_files=output_files,
    )
