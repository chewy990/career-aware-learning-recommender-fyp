"""Own robustness seeded configurations responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import json
import random

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.evaluation import (
    build_metric_summary_rows,
    build_profile_metric_rows,
)
from edu_recommender.models import (
    HYBRID_WEIGHTS,
    Recommendation,
)

from .contracts import COMPONENTS, SEEDED_CONFIGURATION_COUNT, SEEDED_MULTIPLIER_RANGE
from .recommendations import (
    _assert_same_rankings,
    _baseline_summary,
    _ranking_stability,
    _recommend_with_weights,
)


def _run_seeded_configurations(
    resources: list[Resource],
    skill_map: dict[str, dict[str, int]],
    profiles: list[LearnerProfile],
    relevance: dict[str, set[str]],
    baseline: dict[str, list[Recommendation]],
    k_values: tuple[int, ...],
    cutoff: int,
    random_seed: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    configurations = build_seeded_weight_configurations(random_seed)

    config_rows = [
        {
            "configuration_id": configuration_id,
            "random_seed": random_seed,
            "multipliers_json": json.dumps(
                multipliers,
                sort_keys=True,
                separators=(",", ":"),
            ),
            "weights_json": json.dumps(
                {
                    component: round(value, 8)
                    for component, value in weights.items()
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
        }
        for configuration_id, multipliers, weights in configurations
    ]
    baseline_metrics = _baseline_summary(
        baseline,
        profiles,
        relevance,
        k_values,
    )
    result_rows: list[dict[str, object]] = []
    for configuration_id, _, weights in configurations:
        recommendations = _recommend_with_weights(
            resources,
            skill_map,
            profiles,
            weights,
            cutoff,
        )
        if configuration_id == "S000_baseline":
            _assert_same_rankings(baseline, recommendations)
        metrics = build_metric_summary_rows(
            build_profile_metric_rows(
                {"hybrid": recommendations},
                relevance,
                profiles,
                k_values,
            )
        )
        for metric_row in metrics:
            k = int(metric_row["k"])
            baseline_row = baseline_metrics[k]
            overlap, changed = _ranking_stability(
                baseline,
                recommendations,
                k,
            )
            result_rows.append(
                {
                    "configuration_id": configuration_id,
                    "k": k,
                    "precision_at_k": metric_row["precision_at_k"],
                    "recall_at_k": metric_row["recall_at_k"],
                    "ndcg_at_k": metric_row["ndcg_at_k"],
                    "delta_precision": round(
                        float(metric_row["precision_at_k"])
                        - float(baseline_row["precision_at_k"]),
                        4,
                    ),
                    "delta_recall": round(
                        float(metric_row["recall_at_k"])
                        - float(baseline_row["recall_at_k"]),
                        4,
                    ),
                    "delta_ndcg": round(
                        float(metric_row["ndcg_at_k"])
                        - float(baseline_row["ndcg_at_k"]),
                        4,
                    ),
                    "mean_top_k_overlap": overlap,
                    "changed_profile_count": changed,
                }
            )
    return config_rows, result_rows

def build_seeded_weight_configurations(
    random_seed: int,
    count: int = SEEDED_CONFIGURATION_COUNT,
) -> list[tuple[str, dict[str, float], dict[str, float]]]:
    """Build seeded weight configurations deterministically from the supplied evidence."""

    if count < 0:
        raise ValueError("count must not be negative")
    generator = random.Random(random_seed)
    configurations: list[tuple[str, dict[str, float], dict[str, float]]] = [
        (
            "S000_baseline",
            {component: 1.0 for component in COMPONENTS},
            dict(HYBRID_WEIGHTS),
        )
    ]
    for index in range(1, count + 1):
        multipliers = {
            component: round(
                generator.uniform(*SEEDED_MULTIPLIER_RANGE),
                4,
            )
            for component in COMPONENTS
        }
        weights = {
            component: HYBRID_WEIGHTS[component] * multipliers[component]
            for component in COMPONENTS
        }
        configurations.append(
            (f"S{index:03d}", multipliers, weights)
        )
    return configurations
