"""Define immutable pipeline paths and experiment settings.

This module contains configuration only. It must not run phases or write files.
"""

from __future__ import annotations

from pathlib import Path

from edu_recommender.evaluation import DEFAULT_K_VALUES

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
MODELS = ["popularity", "content_based", "hybrid"]
TOP_K = 5
EVALUATION_K_VALUES = DEFAULT_K_VALUES
RECOMMENDATION_CUTOFF = max(EVALUATION_K_VALUES)
RANDOM_SEED = 42
MANIFEST_FILENAME = "run_manifest.json"

def _package_sources(package_name: str) -> list[str]:
    """Return the stable source list for a recommender package."""
    package = ROOT / "src" / "edu_recommender" / package_name
    return [
        path.relative_to(ROOT).as_posix()
        for path in sorted(package.glob("*.py"))
    ]


# Manifest source order is stable across operating systems. Refactor-only source
# changes are expected to alter code hashes and the configuration fingerprint.
CODE_FILES = tuple(
    sorted(
        [
            "src/run_pipeline.py",
            *(
                path.relative_to(ROOT).as_posix()
                for path in sorted((ROOT / "src" / "pipeline").glob("*.py"))
            ),
            "src/edu_recommender/data.py",
            *_package_sources("models"),
            "src/edu_recommender/text.py",
            *(
                source
                for phase in (
                    "validation",
                    "eda",
                    "evaluation",
                    "robustness",
                    "statistical_comparison",
                    "prerequisite_experiment",
                )
                for source in _package_sources(phase)
            ),
        ]
    )
)
