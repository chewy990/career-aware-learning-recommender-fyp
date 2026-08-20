"""Run the frozen counterfactual behavior experiment."""

from __future__ import annotations

import argparse
from pathlib import Path

from edu_recommender.final_robustness import run_counterfactual_experiment


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/counterfactual_behavior_run"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_args()
    root = Path(__file__).resolve().parents[1]
    run_counterfactual_experiment(
        arguments.data_dir.resolve(),
        root / "docs" / "final_robustness_protocol.md",
        arguments.output_dir.resolve(),
        Path(__file__).resolve(),
    )
