"""Own robustness sensitivity responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.evaluation import (
    build_metric_summary_rows,
    build_profile_metric_rows,
)
from edu_recommender.models import (
    HYBRID_WEIGHTS,
    Recommendation,
)

from .contracts import COMPONENTS, SENSITIVITY_MULTIPLIERS
from .recommendations import (
    _baseline_summary,
    _ranking_stability,
    _recommend_with_weights,
)


def _run_weight_sensitivity(
    resources: list[Resource],
    skill_map: dict[str, dict[str, int]],
    profiles: list[LearnerProfile],
    relevance: dict[str, set[str]],
    baseline: dict[str, list[Recommendation]],
    k_values: tuple[int, ...],
    cutoff: int,
) -> list[dict[str, object]]:
    baseline_metrics = _baseline_summary(
        baseline,
        profiles,
        relevance,
        k_values,
    )
    rows: list[dict[str, object]] = []
    for component in COMPONENTS:
        for multiplier in SENSITIVITY_MULTIPLIERS:
            weight_value = HYBRID_WEIGHTS[component] * multiplier
            weights = {**HYBRID_WEIGHTS, component: weight_value}
            recommendations = _recommend_with_weights(
                resources,
                skill_map,
                profiles,
                weights,
                cutoff,
            )
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
                rows.append(
                    {
                        "component": component,
                        "multiplier": multiplier,
                        "weight_value": round(weight_value, 6),
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
    return rows
