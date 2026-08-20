"""Run the frozen leave-one-profile-out stability experiment."""

from __future__ import annotations

import argparse
from pathlib import Path

from edu_recommender.final_robustness import run_leave_one_out_experiment


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile-differences",
        type=Path,
        default=Path(
            "outputs/readiness_gated_alignment_experiment_run/"
            "profile_differences_at_5.csv"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/leave_one_profile_out_run"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_args()
    root = Path(__file__).resolve().parents[1]
    run_leave_one_out_experiment(
        arguments.profile_differences.resolve(),
        root / "docs" / "final_robustness_protocol.md",
        arguments.output_dir.resolve(),
        Path(__file__).resolve(),
    )
