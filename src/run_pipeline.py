"""Command-line entry point for the reproducible recommender pipeline.

Implementation belongs in `pipeline`; this module only parses arguments,
exposes test-configurable paths, and converts validation failures to exit 1.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from edu_recommender.validation import DataValidationError
from pipeline.config import DATA_DIR as DEFAULT_DATA_DIR
from pipeline.config import OUTPUT_DIR as DEFAULT_OUTPUT_DIR
from pipeline.orchestrator import run_pipeline

# Tests and existing scripts patch these public module globals.
DATA_DIR = DEFAULT_DATA_DIR
OUTPUT_DIR = DEFAULT_OUTPUT_DIR


def main() -> None:
    """Run the pipeline using the currently configured data and output paths."""
    run_pipeline(DATA_DIR, OUTPUT_DIR)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate data and run the recommender evaluation pipeline."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "Directory for generated artifacts. Defaults to the repository outputs "
            "folder; use a separate directory to preserve an existing result set."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_args()
    if arguments.output_dir is not None:
        OUTPUT_DIR = arguments.output_dir.resolve()
    try:
        main()
    except DataValidationError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from None
