"""Run the pre-declared readiness-gated weak-skill experiment."""

from __future__ import annotations

import argparse
from pathlib import Path

from edu_recommender.weak_skill_alignment_experiment import (
    GATED_VARIANT_MODEL,
    ReadinessGatedWeakSkillAlignmentSuite,
    build_gated_variant_recommendations,
)
from run_weak_skill_alignment_experiment import run

EXPERIMENT_VERSION = "1"
HYPOTHESIS = (
    "At the unchanged 0.15 weight, replacing broad pathway job-skill alignment "
    "with declared weak-skill alignment multiplied by the existing difficulty "
    "and prerequisite signals retains the weak-case gains without material "
    "pathway or readiness regressions."
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/readiness_gated_alignment_experiment_run"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_args()
    run(
        arguments.data_dir.resolve(),
        arguments.output_dir.resolve(),
        variant_model=GATED_VARIANT_MODEL,
        variant_suite_factory=ReadinessGatedWeakSkillAlignmentSuite,
        variant_builder=build_gated_variant_recommendations,
        experiment_version=EXPERIMENT_VERSION,
        hypothesis=HYPOTHESIS,
        additional_code_paths=(Path(__file__).resolve(),),
    )
