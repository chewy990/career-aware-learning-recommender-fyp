"""Run the pre-declared weak-skill-alignment refinement experiment."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from edu_recommender.data import (
    LearnerProfile,
    read_profiles,
    read_relevance_judgements,
    read_resources,
    read_skill_map,
    write_rows,
)
from edu_recommender.evaluation import (
    build_diagnostic_profile_rows,
    build_diagnostic_summary_rows,
    build_metric_summary_rows,
    build_pathway_metric_rows,
    build_profile_metric_rows,
)
from edu_recommender.models import Recommendation, RecommenderSuite
from edu_recommender.weak_skill_alignment_experiment import (
    VARIANT_MODEL,
    WeakSkillAlignmentSuite,
    build_variant_recommendations,
)
from edu_recommender.weak_skill_alignment_experiment.reporting import (
    experiment_decision,
    paired_ndcg_row,
    profile_difference_rows,
    recommendation_rows,
    sha256,
)

BASELINE_MODEL = "hybrid"
K_VALUES = (3, 5, 10)
PRIMARY_K = 5
RECOMMENDATION_CUTOFF = 10
RANDOM_SEED = 42
BOOTSTRAP_REPLICATES = 5000
EXPERIMENT_VERSION = "1"
HYPOTHESIS = (
    "At the unchanged 0.15 weight, replacing broad pathway job-skill "
    "alignment with weighted coverage of declared weak skills that retain "
    "a positive gap improves graded NDCG@5."
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/weak_skill_alignment_experiment_run"),
    )
    return parser.parse_args()


def run(
    data_dir: Path,
    output_dir: Path,
    *,
    variant_model: str = VARIANT_MODEL,
    variant_suite_factory: Callable[..., RecommenderSuite] = WeakSkillAlignmentSuite,
    variant_builder: Callable[
        [RecommenderSuite, list[LearnerProfile], int],
        dict[str, list[Recommendation]],
    ] = build_variant_recommendations,
    experiment_version: str = EXPERIMENT_VERSION,
    hypothesis: str = HYPOTHESIS,
    additional_code_paths: tuple[Path, ...] = (),
) -> None:
    """Run the frozen experiment once and write a separate evidence set."""

    resources = read_resources(data_dir / "resources.csv")
    profiles = read_profiles(data_dir / "learner_profiles.csv")
    skill_map = read_skill_map(data_dir / "skill_map.csv")
    relevance = read_relevance_judgements(
        data_dir / "relevance_judgements.csv",
        data_dir / "relevance_judgements_graded.csv",
    )
    baseline_suite = RecommenderSuite(resources, skill_map)
    variant_suite = variant_suite_factory(resources, skill_map)
    baseline = {
        profile.profile_id: baseline_suite.recommend(
            profile,
            model="hybrid",
            top_k=RECOMMENDATION_CUTOFF,
        )
        for profile in profiles
    }
    variant = variant_builder(
        variant_suite,
        profiles,
        RECOMMENDATION_CUTOFF,
    )
    recommendations = {BASELINE_MODEL: baseline, variant_model: variant}
    profile_rows = build_profile_metric_rows(
        recommendations,
        relevance,
        profiles,
        K_VALUES,
    )
    summary_rows = build_metric_summary_rows(profile_rows)
    pathway_rows = build_pathway_metric_rows(profile_rows)
    skill_gaps = {
        profile.profile_id: baseline_suite.skill_gaps(profile)
        for profile in profiles
    }
    diagnostic_profile_rows = build_diagnostic_profile_rows(
        recommendations,
        profiles,
        resources,
        skill_gaps,
        (PRIMARY_K,),
    )
    diagnostic_rows = build_diagnostic_summary_rows(
        diagnostic_profile_rows,
        recommendations,
        resources,
        (PRIMARY_K,),
    )
    paired_row = paired_ndcg_row(
        profile_rows,
        BASELINE_MODEL,
        variant_model,
        PRIMARY_K,
        RANDOM_SEED,
        BOOTSTRAP_REPLICATES,
    )
    profile_differences = profile_difference_rows(
        profile_rows,
        BASELINE_MODEL,
        variant_model,
        PRIMARY_K,
    )
    decision = experiment_decision(
        summary_rows,
        pathway_rows,
        profile_differences,
        diagnostic_rows,
        BASELINE_MODEL,
        variant_model,
        PRIMARY_K,
    )

    output_dir.mkdir(parents=True, exist_ok=False)
    tables = {
        "recommendations_variant.csv": (
            ["profile_id", "model", "rank", "resource_id", "title", "provider", "score", "explanation"],
            recommendation_rows(variant),
        ),
        "metrics_by_profile.csv": (
            ["model", "profile_id", "pathway", "k", "recommended_count", "relevant_count", "relevant_hits", "precision_at_k", "recall_at_k", "ndcg_at_k"],
            profile_rows,
        ),
        "metrics_summary.csv": (
            ["model", "k", "profile_count", "precision_at_k", "recall_at_k", "ndcg_at_k"],
            summary_rows,
        ),
        "metrics_by_pathway.csv": (
            ["model", "pathway", "k", "profile_count", "precision_at_k", "recall_at_k", "ndcg_at_k"],
            pathway_rows,
        ),
        "diagnostics_at_5.csv": (list(diagnostic_rows[0]), diagnostic_rows),
        "profile_differences_at_5.csv": (
            ["profile_id", "pathway", "baseline_ndcg_at_5", "variant_ndcg_at_5", "difference"],
            profile_differences,
        ),
        "paired_graded_ndcg_at_5.csv": (list(paired_row), [paired_row]),
    }
    for filename, (fieldnames, rows) in tables.items():
        write_rows(output_dir / filename, fieldnames, rows)

    protocol = {
        "version": experiment_version,
        "analysis_status": "adaptive_exploratory",
        "independent_validation": False,
        "hypothesis": hypothesis,
        "changed_signal": "job_skill_alignment",
        "unchanged": [
            "all weights",
            "all other signals",
            "candidate eligibility",
            "resource data",
            "skill map",
            "learner profiles",
            "graded labels",
        ],
        "primary_metric": "macro graded NDCG@5",
        "decision_thresholds": {
            "minimum_macro_ndcg_at_5_delta": 0.01,
            "minimum_weak_case_mean_delta": 0.0,
            "maximum_pathway_ndcg_at_5_drop": 0.03,
            "maximum_readiness_rate_drop": 0.05,
        },
    }
    _write_json(output_dir / "protocol.json", protocol)
    _write_json(output_dir / "decision.json", decision)
    input_paths = [
        data_dir / "resources.csv",
        data_dir / "skill_map.csv",
        data_dir / "learner_profiles.csv",
        data_dir / "relevance_judgements.csv",
        data_dir / "relevance_judgements_graded.csv",
    ]
    source_dir = Path(__file__).resolve().parent
    code_paths = [
        Path(__file__).resolve(),
        source_dir
        / "edu_recommender"
        / "weak_skill_alignment_experiment"
        / "__init__.py",
        source_dir
        / "edu_recommender"
        / "weak_skill_alignment_experiment"
        / "service.py",
        source_dir
        / "edu_recommender"
        / "weak_skill_alignment_experiment"
        / "reporting.py",
        *additional_code_paths,
    ]
    manifest = {
        "experiment_version": experiment_version,
        "random_seed": RANDOM_SEED,
        "input_sha256": {path.name: sha256(path) for path in input_paths},
        "code_sha256": {
            path.relative_to(source_dir).as_posix(): sha256(path)
            for path in sorted(set(code_paths))
        },
        "output_sha256": {
            path.name: sha256(path)
            for path in sorted(output_dir.iterdir())
            if path.is_file()
        },
    }
    _write_json(output_dir / "manifest.json", manifest)
    print(json.dumps(decision, indent=2, sort_keys=True))


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    arguments = _parse_args()
    run(arguments.data_dir.resolve(), arguments.output_dir.resolve())
