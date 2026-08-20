"""Own robustness ablation responsibilities.

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

from .contracts import COMPONENTS
from .recommendations import (
    _assert_same_rankings,
    _baseline_summary,
    _ranking_stability,
    _recommend_with_weights,
)


def _run_ablation(
    resources: list[Resource],
    skill_map: dict[str, dict[str, int]],
    profiles: list[LearnerProfile],
    relevance: dict[str, set[str]],
    baseline: dict[str, list[Recommendation]],
    k_values: tuple[int, ...],
    cutoff: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    configurations = [("full_hybrid", "", dict(HYBRID_WEIGHTS))]
    configurations.extend(
        (
            f"without_{component}",
            component,
            {**HYBRID_WEIGHTS, component: 0.0},
        )
        for component in COMPONENTS
    )
    baseline_metrics = _baseline_summary(
        baseline,
        profiles,
        relevance,
        k_values,
    )
    summary_rows: list[dict[str, object]] = []
    profile_rows: list[dict[str, object]] = []
    for configuration, removed_component, weights in configurations:
        recommendations = _recommend_with_weights(
            resources,
            skill_map,
            profiles,
            weights,
            cutoff,
        )
        if configuration == "full_hybrid":
            _assert_same_rankings(baseline, recommendations)
        current_profile_rows = build_profile_metric_rows(
            {"hybrid": recommendations},
            relevance,
            profiles,
            k_values,
        )
        current_summary = build_metric_summary_rows(current_profile_rows)
        for row in current_profile_rows:
            profile_rows.append(
                {
                    "configuration": configuration,
                    "removed_component": removed_component,
                    **{
                        key: value
                        for key, value in row.items()
                        if key != "model"
                    },
                }
            )
        for row in current_summary:
            k = int(row["k"])
            baseline_row = baseline_metrics[k]
            overlap, changed = _ranking_stability(
                baseline,
                recommendations,
                k,
            )
            summary_rows.append(
                {
                    "configuration": configuration,
                    "removed_component": removed_component,
                    "k": k,
                    "precision_at_k": row["precision_at_k"],
                    "recall_at_k": row["recall_at_k"],
                    "ndcg_at_k": row["ndcg_at_k"],
                    "delta_precision": round(
                        float(row["precision_at_k"])
                        - float(baseline_row["precision_at_k"]),
                        4,
                    ),
                    "delta_recall": round(
                        float(row["recall_at_k"])
                        - float(baseline_row["recall_at_k"]),
                        4,
                    ),
                    "delta_ndcg": round(
                        float(row["ndcg_at_k"])
                        - float(baseline_row["ndcg_at_k"]),
                        4,
                    ),
                    "mean_top_k_overlap": overlap,
                    "changed_profile_count": changed,
                }
            )
    return summary_rows, profile_rows
