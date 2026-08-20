"""Run validation, analysis, evaluation, reporting, and manifest generation.

This module owns pipeline sequence and output hand-offs. Phase modules own their
scientific calculations; the manifest records reproducibility metadata only.
"""

from __future__ import annotations

from pathlib import Path

from edu_recommender.data import (
    read_profiles,
    read_relevance_judgements,
    read_resources,
    read_skill_map,
    write_rows,
)
from edu_recommender.eda import generate_eda
from edu_recommender.evaluation import DEFAULT_BOOTSTRAP_REPLICATES, generate_evaluation
from edu_recommender.models import Recommendation, RecommenderSuite
from edu_recommender.prerequisite_experiment import generate_prerequisite_experiment
from edu_recommender.robustness import generate_robustness_analysis
from edu_recommender.statistical_comparison import generate_statistical_comparison
from edu_recommender.validation import validate_data_dir
from pipeline.config import (
    EVALUATION_K_VALUES,
    MANIFEST_FILENAME,
    MODELS,
    RANDOM_SEED,
    RECOMMENDATION_CUTOFF,
)
from pipeline.html_report import _write_html_report
from pipeline.manifest import _write_run_manifest
from pipeline.recommendations import _recommendation_rows


def run_pipeline(data_dir: Path, output_dir: Path) -> None:
    """Validate inputs, run every scientific phase, and write reproducible artifacts."""

    validation = validate_data_dir(data_dir)
    write_rows(
        output_dir / "data_validation.csv",
        ["dataset", "check", "status", "details"],
        validation.as_rows(),
    )

    resources = read_resources(data_dir / "resources.csv")
    skill_map = read_skill_map(data_dir / "skill_map.csv")
    profiles = read_profiles(data_dir / "learner_profiles.csv")
    relevance = read_relevance_judgements(
        data_dir / "relevance_judgements.csv",
        data_dir / "relevance_judgements_graded.csv",
    )
    eda_result = generate_eda(
        resources,
        profiles,
        relevance,
        skill_map,
        validation.row_counts,
        output_dir,
    )

    suite = RecommenderSuite(resources, skill_map)
    recommendations_by_model: dict[str, dict[str, list[Recommendation]]] = {}

    for model in MODELS:
        model_recommendations: dict[str, list[Recommendation]] = {}
        rows: list[dict[str, object]] = []
        for profile in profiles:
            recommendations = suite.recommend(
                profile,
                model=model,
                top_k=RECOMMENDATION_CUTOFF,
            )
            model_recommendations[profile.profile_id] = recommendations
            rows.extend(_recommendation_rows(recommendations))
        recommendations_by_model[model] = model_recommendations
        write_rows(
            output_dir / f"recommendations_{model}.csv",
            ["profile_id", "model", "rank", "resource_id", "title", "provider", "score", "explanation"],
            rows,
        )

    evaluation_result = generate_evaluation(
        recommendations_by_model,
        relevance,
        profiles,
        resources,
        {
            profile.profile_id: suite.skill_gaps(profile)
            for profile in profiles
        },
        output_dir,
        k_values=EVALUATION_K_VALUES,
        random_seed=RANDOM_SEED,
        bootstrap_replicates=DEFAULT_BOOTSTRAP_REPLICATES,
    )
    robustness_result = generate_robustness_analysis(
        resources,
        skill_map,
        profiles,
        relevance,
        recommendations_by_model,
        evaluation_result,
        output_dir,
        k_values=EVALUATION_K_VALUES,
        random_seed=RANDOM_SEED,
    )
    statistical_result = generate_statistical_comparison(
        evaluation_result,
        recommendations_by_model,
        profiles,
        resources,
        relevance,
        output_dir,
        random_seed=RANDOM_SEED,
        bootstrap_replicates=DEFAULT_BOOTSTRAP_REPLICATES,
    )
    prerequisite_result = generate_prerequisite_experiment(
        suite,
        recommendations_by_model["hybrid"],
        profiles,
        resources,
        relevance,
        output_dir,
        k_values=EVALUATION_K_VALUES,
        random_seed=RANDOM_SEED,
        bootstrap_replicates=DEFAULT_BOOTSTRAP_REPLICATES,
    )
    _write_html_report(
        evaluation_result,
        robustness_result,
        statistical_result,
        prerequisite_result,
        recommendations_by_model,
        eda_result,
        output_dir,
    )
    _write_run_manifest(
        validation.row_counts,
        eda_result.output_files,
        evaluation_result.output_files,
        robustness_result.output_files,
        statistical_result.output_files,
        prerequisite_result.output_files,
        data_dir,
        output_dir,
    )

    print(f"Pipeline completed. Outputs written to: {output_dir}")
    print(
        f"Data validation passed for {sum(validation.row_counts.values())} rows "
        f"across {len(validation.row_counts)} CSV files."
    )
    print(f"Run manifest written to: {output_dir / MANIFEST_FILENAME}")
    print(
        f"Phase 2 EDA generated {len(eda_result.output_files)} "
        "tables, figures, and summary artifacts."
    )
    print(
        f"Phase 3 evaluation generated {len(evaluation_result.output_files)} "
        "tables, figures, and summary artifacts."
    )
    print(
        f"Phase 4 robustness analysis generated "
        f"{len(robustness_result.output_files)} "
        "tables, figures, and summary artifacts."
    )
    print(
        f"Phase 5 statistical comparison generated "
        f"{len(statistical_result.output_files)} "
        "tables, figures, and summary artifacts."
    )
    print(
        f"Hard-prerequisite experiment generated "
        f"{len(prerequisite_result.output_files)} "
        "tables, figures, and summary artifacts."
    )
    for row in evaluation_result.summary_rows:
        print(
            f"{row['model']}: "
            f"Precision@{row['k']}={row['precision_at_k']}, "
            f"Recall@{row['k']}={row['recall_at_k']}, "
            f"NDCG@{row['k']}={row['ndcg_at_k']}"
        )

