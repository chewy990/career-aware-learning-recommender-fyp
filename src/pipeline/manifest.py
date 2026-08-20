"""Generate reproducibility metadata and artifact fingerprints.

The manifest describes how outputs were produced; it is not a scientific result.
Source paths are sorted deterministically and every fingerprint is content based.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from edu_recommender.eda import EDA_VERSION
from edu_recommender.evaluation import DEFAULT_BOOTSTRAP_REPLICATES, EVALUATION_VERSION
from edu_recommender.models import HYBRID_WEIGHTS, POPULARITY_WEIGHTS
from edu_recommender.prerequisite_experiment import (
    PREREQUISITE_EXPERIMENT_VERSION,
)
from edu_recommender.prerequisite_experiment import (
    VARIANT_MODEL as PREREQUISITE_VARIANT_MODEL,
)
from edu_recommender.robustness import (
    FAILURE_THRESHOLDS,
    ROBUSTNESS_VERSION,
    SEEDED_CONFIGURATION_COUNT,
    SEEDED_MULTIPLIER_RANGE,
    SENSITIVITY_MULTIPLIERS,
)
from edu_recommender.statistical_comparison import (
    AUDIT_ITEMS_PER_PATHWAY,
    BASELINE_MODELS,
    SIGNIFICANCE_LEVEL,
    STATISTICAL_COMPARISON_VERSION,
)
from pipeline.config import (
    CODE_FILES,
    EVALUATION_K_VALUES,
    MANIFEST_FILENAME,
    MODELS,
    RANDOM_SEED,
    RECOMMENDATION_CUTOFF,
    ROOT,
    TOP_K,
)


def _write_run_manifest(
    row_counts: dict[str, int],
    eda_output_files: tuple[str, ...],
    evaluation_output_files: tuple[str, ...],
    robustness_output_files: tuple[str, ...],
    statistical_output_files: tuple[str, ...],
    prerequisite_output_files: tuple[str, ...],
    data_dir: Path,
    output_dir: Path,
) -> None:
    output_names = [
        "data_validation.csv",
        *eda_output_files,
        *(f"recommendations_{model}.csv" for model in MODELS),
        *evaluation_output_files,
        *robustness_output_files,
        *statistical_output_files,
        *prerequisite_output_files,
        "report.html",
    ]
    input_files = {
        name: {
            "rows": row_counts[name],
            "sha256": _sha256(data_dir / name),
        }
        for name in sorted(row_counts)
    }
    code_files = {
        name: {"sha256": _sha256(ROOT / name)}
        for name in CODE_FILES
    }
    model_settings = {
        "popularity": {"weights": POPULARITY_WEIGHTS},
        "content_based": {
            "representation": "TF-IDF",
            "similarity": "cosine",
        },
        "hybrid": {"weights": HYBRID_WEIGHTS},
        PREREQUISITE_VARIANT_MODEL: {
            "base_model": "hybrid",
            "weights": HYBRID_WEIGHTS,
            "candidate_rule": (
                "all prerequisites completed or current skill level >= 1"
            ),
            "experimental_only": True,
        },
    }
    reproducibility_payload = {
        "code_files": code_files,
        "input_files": input_files,
        "models": MODELS,
        "model_settings": model_settings,
        "eda_version": EDA_VERSION,
        "evaluation_version": EVALUATION_VERSION,
        "robustness_version": ROBUSTNESS_VERSION,
        "statistical_comparison_version": STATISTICAL_COMPARISON_VERSION,
        "prerequisite_experiment_version": PREREQUISITE_EXPERIMENT_VERSION,
        "bootstrap_replicates": DEFAULT_BOOTSTRAP_REPLICATES,
        "sensitivity_multipliers": list(SENSITIVITY_MULTIPLIERS),
        "seeded_configuration_count": SEEDED_CONFIGURATION_COUNT,
        "seeded_multiplier_range": list(SEEDED_MULTIPLIER_RANGE),
        "failure_thresholds": FAILURE_THRESHOLDS,
        "paired_baselines": list(BASELINE_MODELS),
        "statistical_significance_level": SIGNIFICANCE_LEVEL,
        "planned_paired_comparisons": (
            len(BASELINE_MODELS)
            * 3
            * len(EVALUATION_K_VALUES)
        ),
        "audit_items_per_pathway": AUDIT_ITEMS_PER_PATHWAY,
        "prerequisite_experiment_primary_k": TOP_K,
        "prerequisite_experiment_planned_metrics": [
            "precision_at_k",
            "recall_at_k",
            "ndcg_at_k",
        ],
        "k_values": list(EVALUATION_K_VALUES),
        "recommendation_cutoff": RECOMMENDATION_CUTOFF,
        "random_seed": RANDOM_SEED,
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            reproducibility_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    manifest = {
        "schema_version": 1,
        "run_id": fingerprint[:16],
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "configuration_fingerprint_sha256": fingerprint,
        **reproducibility_payload,
        "output_files": {
            name: {"sha256": _sha256(output_dir / name)}
            for name in output_names
        },
        "manifest_filename": MANIFEST_FILENAME,
        "python_version": sys.version.split()[0],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

