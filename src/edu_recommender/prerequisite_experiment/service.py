"""Own prerequisite experiment service responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

from edu_recommender.data import LearnerProfile, Resource, write_rows
from edu_recommender.evaluation import (
    DEFAULT_BOOTSTRAP_REPLICATES,
    DEFAULT_K_VALUES,
    build_diagnostic_profile_rows,
    build_diagnostic_summary_rows,
    build_metric_summary_rows,
    build_pathway_metric_rows,
    build_profile_metric_rows,
)
from edu_recommender.models import (
    Recommendation,
    RecommenderSuite,
)

from .contracts import (
    BASELINE_MODEL,
    PRIMARY_K,
    VARIANT_MODEL,
    PrerequisiteExperimentResult,
)
from .diagnostics import _validate_experiment
from .eligibility import build_eligible_recommendations
from .findings import build_findings
from .paired_comparison import build_paired_rows
from .profile_changes import build_profile_change_rows
from .reporting import _write_summary
from .targeted_audit import build_targeted_audit


def generate_prerequisite_experiment(
    suite: RecommenderSuite,
    baseline_recommendations: dict[str, list[Recommendation]],
    profiles: list[LearnerProfile],
    resources: list[Resource],
    relevance_judgements: dict[str, set[str]],
    output_dir: Path,
    k_values: tuple[int, ...] = DEFAULT_K_VALUES,
    random_seed: int = 42,
    bootstrap_replicates: int = DEFAULT_BOOTSTRAP_REPLICATES,
) -> PrerequisiteExperimentResult:
    """Run the paired prerequisite experiment and write its owned artifacts."""

    recommendation_cutoff = max(k_values)
    variant_recommendations = build_eligible_recommendations(
        suite,
        profiles,
        recommendation_cutoff,
    )
    recommendations = {
        BASELINE_MODEL: baseline_recommendations,
        VARIANT_MODEL: variant_recommendations,
    }
    skill_gaps = {
        profile.profile_id: suite.skill_gaps(profile)
        for profile in profiles
    }
    profile_rows = build_profile_metric_rows(
        recommendations,
        relevance_judgements,
        profiles,
        k_values,
    )
    summary_rows = build_metric_summary_rows(profile_rows)
    pathway_rows = build_pathway_metric_rows(profile_rows)
    diagnostic_profile_rows = build_diagnostic_profile_rows(
        recommendations,
        profiles,
        resources,
        skill_gaps,
        k_values,
    )
    diagnostic_rows = [
        row
        for row in build_diagnostic_summary_rows(
            diagnostic_profile_rows,
            recommendations,
            resources,
            k_values,
        )
        if int(row["k"]) == PRIMARY_K
    ]
    paired_rows = build_paired_rows(
        profile_rows,
        random_seed=random_seed,
        bootstrap_replicates=bootstrap_replicates,
    )
    profile_change_rows = build_profile_change_rows(
        baseline_recommendations,
        variant_recommendations,
        profiles,
        resources,
        relevance_judgements,
        profile_rows,
        recommendation_cutoff,
    )
    audit_blinded_rows, audit_key_rows = build_targeted_audit(
        profile_change_rows,
        profiles,
        resources,
        relevance_judgements,
        random_seed,
    )
    _validate_experiment(
        variant_recommendations,
        profiles,
        resources,
        recommendation_cutoff,
        diagnostic_rows,
    )
    findings = build_findings(
        summary_rows,
        paired_rows,
        diagnostic_rows,
        profile_change_rows,
        pathway_rows,
    )

    recommendation_rows = [
        {
            "profile_id": recommendation.profile_id,
            "model": recommendation.model,
            "rank": recommendation.rank,
            "resource_id": recommendation.resource_id,
            "title": recommendation.title,
            "provider": recommendation.provider,
            "score": recommendation.score,
            "explanation": recommendation.explanation,
        }
        for profile_id in sorted(variant_recommendations)
        for recommendation in variant_recommendations[profile_id]
    ]
    table_specs = {
        "prerequisite_experiment_recommendations.csv": (
            [
                "profile_id",
                "model",
                "rank",
                "resource_id",
                "title",
                "provider",
                "score",
                "explanation",
            ],
            recommendation_rows,
        ),
        "prerequisite_experiment_metrics_by_profile.csv": (
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
        "prerequisite_experiment_metrics_summary.csv": (
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
        "prerequisite_experiment_metrics_by_pathway.csv": (
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
        "prerequisite_experiment_paired_at_5.csv": (
            [
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
                "variant_wins",
                "ties",
                "variant_losses",
                "exact_permutation_p",
                "exact_permutation_holm_p",
                "wilcoxon_w_plus",
                "wilcoxon_p",
                "wilcoxon_holm_p",
                "holm_significant_at_0_05",
                "bootstrap_replicates",
                "random_seed",
            ],
            paired_rows,
        ),
        "prerequisite_experiment_diagnostics_at_5.csv": (
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
            diagnostic_rows,
        ),
        "prerequisite_experiment_profile_changes.csv": (
            [
                "profile_id",
                "pathway",
                "ranking_changed",
                "top_5_changed",
                "top_10_overlap",
                "baseline_invalid_at_5_count",
                "variant_invalid_at_5_count",
                "baseline_invalid_count",
                "variant_invalid_count",
                "baseline_invalid_ids",
                "removed_ids",
                "replacement_ids",
                "relevant_replacement_count",
                "baseline_ndcg_at_5",
                "variant_ndcg_at_5",
                "ndcg_at_5_difference",
                "baseline_top_5",
                "variant_top_5",
            ],
            profile_change_rows,
        ),
        "prerequisite_experiment_audit_blinded.csv": (
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
        "prerequisite_experiment_audit_key.csv": (
            [
                "audit_item_id",
                "profile_id",
                "resource_id",
                "current_label",
                "experiment_role",
            ],
            audit_key_rows,
        ),
        "prerequisite_experiment_findings.csv": (
            ["title", "finding", "implication"],
            list(findings),
        ),
    }
    for filename, (fieldnames, rows) in table_specs.items():
        write_rows(output_dir / filename, fieldnames, rows)

    from .figures import _write_figures

    figure_files = _write_figures(
        summary_rows,
        profile_rows,
        diagnostic_rows,
        output_dir,
    )
    _write_summary(findings, figure_files, output_dir)
    output_files = (
            *table_specs,
            "prerequisite_experiment_summary.md",
            *figure_files,
        )
    return PrerequisiteExperimentResult(
        variant_recommendations=variant_recommendations,
        profile_metric_rows=tuple(profile_rows),
        summary_rows=tuple(summary_rows),
        pathway_rows=tuple(pathway_rows),
        paired_rows=tuple(paired_rows),
        diagnostic_rows=tuple(diagnostic_rows),
        profile_change_rows=tuple(profile_change_rows),
        audit_blinded_rows=tuple(audit_blinded_rows),
        audit_key_rows=tuple(audit_key_rows),
        findings=findings,
        output_files=output_files,
    )
