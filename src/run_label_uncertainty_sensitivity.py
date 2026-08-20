"""Run the frozen label-uncertainty sensitivity experiment."""

from __future__ import annotations

import argparse
from pathlib import Path

from edu_recommender.final_robustness import run_label_sensitivity_experiment


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--graded-run-dir",
        type=Path,
        default=Path("outputs/graded_relevance_run"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/label_uncertainty_sensitivity_run"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_args()
    run_label_sensitivity_experiment(
        arguments.data_dir.resolve(),
        arguments.graded_run_dir.resolve(),
        arguments.output_dir.resolve(),
        Path(__file__).resolve(),
    )
