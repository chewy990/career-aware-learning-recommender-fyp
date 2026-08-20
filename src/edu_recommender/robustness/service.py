"""Own robustness service responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

from edu_recommender.data import LearnerProfile, Resource, write_rows
from edu_recommender.evaluation import (
    EvaluationResult,
)
from edu_recommender.models import (
    Recommendation,
)

from .ablation import _run_ablation
from .contracts import COMPONENTS, RobustnessResult
from .contributions import _build_component_contribution_rows
from .failures import _build_failure_rows
from .findings import _build_findings
from .reporting import _write_summary
from .seeded_configurations import _run_seeded_configurations
from .sensitivity import _run_weight_sensitivity


def generate_robustness_analysis(
    resources: list[Resource],
    skill_map: dict[str, dict[str, int]],
    profiles: list[LearnerProfile],
    relevance_judgements: dict[str, set[str]],
    baseline_recommendations: dict[str, dict[str, list[Recommendation]]],
    evaluation_result: EvaluationResult,
    output_dir: Path,
    k_values: tuple[int, ...],
    random_seed: int,
) -> RobustnessResult:
    """Run robustness orchestration with seeded configurations and owned artifacts."""

    baseline_hybrid = baseline_recommendations["hybrid"]
    recommendation_cutoff = max(k_values)

    ablation_summary_rows, ablation_profile_rows = _run_ablation(
        resources,
        skill_map,
        profiles,
        relevance_judgements,
        baseline_hybrid,
        k_values,
        recommendation_cutoff,
    )
    sensitivity_rows = _run_weight_sensitivity(
        resources,
        skill_map,
        profiles,
        relevance_judgements,
        baseline_hybrid,
        k_values,
        recommendation_cutoff,
    )
    seeded_configuration_rows, seeded_result_rows = _run_seeded_configurations(
        resources,
        skill_map,
        profiles,
        relevance_judgements,
        baseline_hybrid,
        k_values,
        recommendation_cutoff,
        random_seed,
    )
    contribution_rows = _build_component_contribution_rows(
        resources,
        skill_map,
        profiles,
        baseline_hybrid,
        example_count=3,
    )
    failure_rows = _build_failure_rows(
        resources,
        profiles,
        baseline_hybrid,
        evaluation_result,
    )
    findings = _build_findings(
        ablation_summary_rows,
        ablation_profile_rows,
        sensitivity_rows,
        seeded_result_rows,
        failure_rows,
    )

    table_specs = {
        "phase4_ablation_summary.csv": (
            [
                "configuration",
                "removed_component",
                "k",
                "precision_at_k",
                "recall_at_k",
                "ndcg_at_k",
                "delta_precision",
                "delta_recall",
                "delta_ndcg",
                "mean_top_k_overlap",
                "changed_profile_count",
            ],
            ablation_summary_rows,
        ),
        "phase4_ablation_profile_metrics.csv": (
            [
                "configuration",
                "removed_component",
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
            ablation_profile_rows,
        ),
        "phase4_weight_sensitivity.csv": (
            [
                "component",
                "multiplier",
                "weight_value",
                "k",
                "precision_at_k",
                "recall_at_k",
                "ndcg_at_k",
                "delta_precision",
                "delta_recall",
                "delta_ndcg",
                "mean_top_k_overlap",
                "changed_profile_count",
            ],
            sensitivity_rows,
        ),
        "phase4_seeded_weight_configs.csv": (
            [
                "configuration_id",
                "random_seed",
                "multipliers_json",
                "weights_json",
            ],
            seeded_configuration_rows,
        ),
        "phase4_seeded_weight_results.csv": (
            [
                "configuration_id",
                "k",
                "precision_at_k",
                "recall_at_k",
                "ndcg_at_k",
                "delta_precision",
                "delta_recall",
                "delta_ndcg",
                "mean_top_k_overlap",
                "changed_profile_count",
            ],
            seeded_result_rows,
        ),
        "phase4_component_contributions.csv": (
            [
                "profile_id",
                "pathway",
                "rank",
                "resource_id",
                "title",
                *(
                    f"raw_{component}"
                    for component in COMPONENTS
                ),
                *(
                    f"contribution_{component}"
                    for component in COMPONENTS
                ),
                "calculated_total_score",
                "pipeline_score",
            ],
            contribution_rows,
        ),
        "phase4_failure_cases.csv": (
            [
                "failure_type",
                "profile_id",
                "pathway",
                "resource_id",
                "rank",
                "severity",
                "observed_value",
                "threshold",
                "details",
            ],
            failure_rows,
        ),
        "phase4_findings.csv": (
            ["title", "finding", "implication"],
            list(findings),
        ),
    }
    for filename, (fieldnames, rows) in table_specs.items():
        write_rows(output_dir / filename, fieldnames, rows)

    from .figures import _write_figures

    figure_files = _write_figures(
        ablation_summary_rows,
        sensitivity_rows,
        seeded_result_rows,
        failure_rows,
        output_dir,
    )
    _write_summary(findings, figure_files, output_dir)
    output_files = (
            *table_specs,
            "phase4_summary.md",
            *figure_files,
        )
    return RobustnessResult(
        ablation_summary_rows=tuple(ablation_summary_rows),
        ablation_profile_rows=tuple(ablation_profile_rows),
        sensitivity_rows=tuple(sensitivity_rows),
        seeded_configuration_rows=tuple(seeded_configuration_rows),
        seeded_result_rows=tuple(seeded_result_rows),
        contribution_rows=tuple(contribution_rows),
        failure_rows=tuple(failure_rows),
        findings=findings,
        output_files=output_files,
    )
