"""Deterministic sensitivity analysis for lower-confidence relevance grades."""

from __future__ import annotations

import csv
from pathlib import Path

from edu_recommender.data import (
    GradedResourceSet,
    read_profiles,
    read_relevance_judgements,
    read_resources,
    read_skill_map,
    write_rows,
)
from edu_recommender.evaluation import (
    build_metric_summary_rows,
    build_pathway_metric_rows,
    build_profile_metric_rows,
)
from edu_recommender.models import RecommenderSuite
from edu_recommender.weak_skill_alignment_experiment import (
    GATED_VARIANT_MODEL,
    ReadinessGatedWeakSkillAlignmentSuite,
    build_gated_variant_recommendations,
)

from .common import write_json, write_manifest

BASELINE_MODEL = "hybrid"
PRIMARY_K = 5
TOP_K = 10
SCENARIOS = (
    "canonical",
    "all_uncertain_down_one",
    "all_uncertain_up_one",
    "confidence_1_down_one",
    "confidence_1_up_one",
)


def run_label_sensitivity_experiment(
    data_dir: Path,
    graded_run_dir: Path,
    output_dir: Path,
    runner_path: Path,
) -> None:
    """Run four frozen grade perturbations without editing canonical labels."""

    resources = read_resources(data_dir / "resources.csv")
    profiles = read_profiles(data_dir / "learner_profiles.csv")
    skill_map = read_skill_map(data_dir / "skill_map.csv")
    relevance = read_relevance_judgements(
        data_dir / "relevance_judgements.csv",
        data_dir / "relevance_judgements_graded.csv",
    )
    confidence = _read_confidence(graded_run_dir)
    confidence_counts = {
        level: sum(value == level for value in confidence.values())
        for level in (1, 2, 3)
    }
    if confidence_counts[1] != 6 or confidence_counts[2] != 44:
        raise ValueError("Expected 6 confidence-1 and 44 confidence-2 grades")

    baseline_suite = RecommenderSuite(resources, skill_map)
    gated_suite = ReadinessGatedWeakSkillAlignmentSuite(resources, skill_map)
    baseline = {
        profile.profile_id: baseline_suite.recommend(
            profile,
            model=BASELINE_MODEL,
            top_k=TOP_K,
        )
        for profile in profiles
    }
    gated = build_gated_variant_recommendations(
        gated_suite,
        profiles,
        TOP_K,
    )
    recommendations = {BASELINE_MODEL: baseline, GATED_VARIANT_MODEL: gated}

    summary_rows: list[dict[str, object]] = []
    profile_rows_out: list[dict[str, object]] = []
    pathway_rows_out: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        scenario_relevance, changed_count = _scenario_relevance(
            relevance,
            confidence,
            scenario,
        )
        profile_rows = build_profile_metric_rows(
            recommendations,
            scenario_relevance,
            profiles,
            (PRIMARY_K,),
        )
        macro_rows = build_metric_summary_rows(profile_rows)
        pathway_rows = build_pathway_metric_rows(profile_rows)
        macro = {str(row["model"]): row for row in macro_rows}
        paired = _paired_profile_rows(profile_rows, scenario)
        pathway = _paired_pathway_rows(pathway_rows, scenario)
        difference = round(
            float(macro[GATED_VARIANT_MODEL]["ndcg_at_k"])
            - float(macro[BASELINE_MODEL]["ndcg_at_k"]),
            6,
        )
        summary_rows.append(
            {
                "scenario": scenario,
                "changed_grade_count": changed_count,
                "baseline_ndcg_at_5": macro[BASELINE_MODEL]["ndcg_at_k"],
                "gated_ndcg_at_5": macro[GATED_VARIANT_MODEL]["ndcg_at_k"],
                "mean_difference": difference,
                "gated_wins": sum(float(row["difference"]) > 0 for row in paired),
                "ties": sum(float(row["difference"]) == 0 for row in paired),
                "gated_losses": sum(float(row["difference"]) < 0 for row in paired),
                "minimum_pathway_difference": min(
                    float(row["difference"]) for row in pathway
                ),
                "direction_positive": difference > 0,
            }
        )
        profile_rows_out.extend(paired)
        pathway_rows_out.extend(pathway)

    perturbed = [row for row in summary_rows if row["scenario"] != "canonical"]
    decision = {
        "criterion": "gated-minus-production macro graded NDCG@5 stays positive",
        "passed": all(bool(row["direction_positive"]) for row in perturbed),
        "minimum_mean_difference": min(
            float(row["mean_difference"]) for row in perturbed
        ),
        "maximum_mean_difference": max(
            float(row["mean_difference"]) for row in perturbed
        ),
        "canonical_grades_modified": False,
        "interpretation_limit": "Sensitivity to declared confidence shifts, not independent validation.",
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    write_rows(
        output_dir / "scenario_summary.csv",
        list(summary_rows[0]),
        summary_rows,
    )
    write_rows(
        output_dir / "profile_differences.csv",
        list(profile_rows_out[0]),
        profile_rows_out,
    )
    write_rows(
        output_dir / "pathway_differences.csv",
        list(pathway_rows_out[0]),
        pathway_rows_out,
    )
    write_json(output_dir / "decision.json", decision)
    write_json(
        output_dir / "protocol.json",
        {
            "version": "1",
            "frozen_protocol": "docs/final_robustness_protocol.md",
            "scenarios": list(SCENARIOS[1:]),
            "confidence_counts": confidence_counts,
            "primary_metric": "gated-minus-production macro graded NDCG@5",
            "stability_rule": "positive in every perturbed scenario",
        },
    )
    project_root = data_dir.parent
    write_manifest(
        output_dir,
        "label_uncertainty_sensitivity",
        [
            data_dir / "resources.csv",
            data_dir / "skill_map.csv",
            data_dir / "learner_profiles.csv",
            data_dir / "relevance_judgements.csv",
            data_dir / "relevance_judgements_graded.csv",
            graded_run_dir / "input" / "graded_relevance_completed.csv",
            graded_run_dir / "input" / "graded_relevance_key.csv",
            project_root / "docs" / "final_robustness_protocol.md",
        ],
        _code_paths(project_root, runner_path),
    )


def _read_confidence(graded_run_dir: Path) -> dict[tuple[str, str], int]:
    key_path = graded_run_dir / "input" / "graded_relevance_key.csv"
    completed_path = graded_run_dir / "input" / "graded_relevance_completed.csv"
    with key_path.open(newline="", encoding="utf-8") as file:
        key = {
            row["grading_item_id"]: (row["profile_id"], row["resource_id"])
            for row in csv.DictReader(file)
        }
    with completed_path.open(newline="", encoding="utf-8") as file:
        return {
            key[row["grading_item_id"]]: int(row["reviewer_confidence"])
            for row in csv.DictReader(file)
        }


def _scenario_relevance(
    relevance: dict[str, set[str]],
    confidence: dict[tuple[str, str], int],
    scenario: str,
) -> tuple[dict[str, set[str]], int]:
    changed = 0
    result: dict[str, set[str]] = {}
    for profile_id, relevant_ids in relevance.items():
        grades: dict[str, int] = {}
        for resource_id, canonical in getattr(relevant_ids, "grades", {}).items():
            level = confidence[(profile_id, resource_id)]
            grade = int(canonical)
            if scenario == "all_uncertain_down_one" and level <= 2:
                grade = max(1, grade - 1)
            elif scenario == "all_uncertain_up_one" and level <= 2:
                grade = min(3, grade + 1)
            elif scenario == "confidence_1_down_one" and level == 1:
                grade = max(1, grade - 1)
            elif scenario == "confidence_1_up_one" and level == 1:
                grade = min(3, grade + 1)
            changed += grade != int(canonical)
            grades[resource_id] = grade
        result[profile_id] = GradedResourceSet(set(relevant_ids), grades)
    return result, changed


def _paired_profile_rows(
    rows: list[dict[str, object]],
    scenario: str,
) -> list[dict[str, object]]:
    lookup = {(str(row["model"]), str(row["profile_id"])): row for row in rows}
    profile_ids = sorted(profile_id for model, profile_id in lookup if model == BASELINE_MODEL)
    return [
        {
            "scenario": scenario,
            "profile_id": profile_id,
            "pathway": lookup[(BASELINE_MODEL, profile_id)]["pathway"],
            "baseline_ndcg_at_5": lookup[(BASELINE_MODEL, profile_id)]["ndcg_at_k"],
            "gated_ndcg_at_5": lookup[(GATED_VARIANT_MODEL, profile_id)]["ndcg_at_k"],
            "difference": round(
                float(lookup[(GATED_VARIANT_MODEL, profile_id)]["ndcg_at_k"])
                - float(lookup[(BASELINE_MODEL, profile_id)]["ndcg_at_k"]),
                6,
            ),
        }
        for profile_id in profile_ids
    ]


def _paired_pathway_rows(
    rows: list[dict[str, object]],
    scenario: str,
) -> list[dict[str, object]]:
    lookup = {(str(row["model"]), str(row["pathway"])): row for row in rows}
    pathways = sorted(pathway for model, pathway in lookup if model == BASELINE_MODEL)
    return [
        {
            "scenario": scenario,
            "pathway": pathway,
            "baseline_ndcg_at_5": lookup[(BASELINE_MODEL, pathway)]["ndcg_at_k"],
            "gated_ndcg_at_5": lookup[(GATED_VARIANT_MODEL, pathway)]["ndcg_at_k"],
            "difference": round(
                float(lookup[(GATED_VARIANT_MODEL, pathway)]["ndcg_at_k"])
                - float(lookup[(BASELINE_MODEL, pathway)]["ndcg_at_k"]),
                6,
            ),
        }
        for pathway in pathways
    ]


def _code_paths(project_root: Path, runner_path: Path) -> list[Path]:
    source = project_root / "src"
    return [
        Path(__file__).resolve(),
        Path(__file__).with_name("common.py").resolve(),
        runner_path.resolve(),
        source / "edu_recommender" / "models" / "suite.py",
        source / "edu_recommender" / "models" / "signals.py",
        source / "edu_recommender" / "evaluation" / "ranking_metrics.py",
        source / "edu_recommender" / "weak_skill_alignment_experiment" / "service.py",
    ]
