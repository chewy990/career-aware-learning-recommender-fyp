"""Own evaluation metrics responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.data import LearnerProfile
from edu_recommender.models import Recommendation

from .contracts import METRIC_NAMES
from .ranking_metrics import ndcg_at_k, precision_at_k, recall_at_k
from .reporting import (
    _models_from_rows,
    _ordered_models,
    _rounded_mean,
    _validate_k_values,
)


def evaluate_recommendations(
    recommendations_by_model: dict[str, dict[str, list[Recommendation]]],
    relevance_judgements: dict[str, set[str]],
    k: int,
) -> list[dict[str, object]]:
    """Backward-compatible macro metric summary for one K value."""
    _validate_k_values((k,))
    rows: list[dict[str, object]] = []
    for model in _ordered_models(recommendations_by_model):
        precision_values: list[float] = []
        recall_values: list[float] = []
        ndcg_values: list[float] = []
        for profile_id in sorted(recommendations_by_model[model]):
            relevant_ids = relevance_judgements[profile_id]
            ranked_ids = [
                recommendation.resource_id
                for recommendation in recommendations_by_model[model][profile_id]
            ]
            precision_values.append(precision_at_k(ranked_ids, relevant_ids, k))
            recall_values.append(recall_at_k(ranked_ids, relevant_ids, k))
            ndcg_values.append(ndcg_at_k(ranked_ids, relevant_ids, k))
        rows.append(
            {
                "model": model,
                "k": k,
                "precision_at_k": _rounded_mean(precision_values),
                "recall_at_k": _rounded_mean(recall_values),
                "ndcg_at_k": _rounded_mean(ndcg_values),
            }
        )
    return rows

def build_profile_metric_rows(
    recommendations_by_model: dict[str, dict[str, list[Recommendation]]],
    relevance_judgements: dict[str, set[str]],
    profiles: list[LearnerProfile],
    k_values: tuple[int, ...],
) -> list[dict[str, object]]:
    """Build profile metric rows deterministically from the supplied evidence."""

    _validate_k_values(k_values)
    profile_lookup = {profile.profile_id: profile for profile in profiles}
    rows: list[dict[str, object]] = []
    for model in _ordered_models(recommendations_by_model):
        for profile_id in sorted(recommendations_by_model[model]):
            recommendations = recommendations_by_model[model][profile_id]
            ranked_ids = [item.resource_id for item in recommendations]
            relevant_ids = relevance_judgements[profile_id]
            for k in k_values:
                top_ids = ranked_ids[:k]
                hits = sum(resource_id in relevant_ids for resource_id in top_ids)
                rows.append(
                    {
                        "model": model,
                        "profile_id": profile_id,
                        "pathway": profile_lookup[profile_id].target_pathway,
                        "k": k,
                        "recommended_count": len(top_ids),
                        "relevant_count": len(relevant_ids),
                        "relevant_hits": hits,
                        "precision_at_k": round(
                            precision_at_k(ranked_ids, relevant_ids, k),
                            6,
                        ),
                        "recall_at_k": round(
                            recall_at_k(ranked_ids, relevant_ids, k),
                            6,
                        ),
                        "ndcg_at_k": round(
                            ndcg_at_k(ranked_ids, relevant_ids, k),
                            6,
                        ),
                    }
                )
    return rows

def build_metric_summary_rows(
    profile_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Build metric summary rows deterministically from the supplied evidence."""

    rows: list[dict[str, object]] = []
    for model in _models_from_rows(profile_rows):
        for k in sorted({int(row["k"]) for row in profile_rows}):
            group = [
                row
                for row in profile_rows
                if row["model"] == model and int(row["k"]) == k
            ]
            rows.append(
                {
                    "model": model,
                    "k": k,
                    "profile_count": len(group),
                    **{
                        metric: _rounded_mean(
                            [float(row[metric]) for row in group]
                        )
                        for metric in METRIC_NAMES
                    },
                }
            )
    return rows

def build_pathway_metric_rows(
    profile_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Build pathway metric rows deterministically from the supplied evidence."""

    rows: list[dict[str, object]] = []
    pathways = sorted({str(row["pathway"]) for row in profile_rows})
    for model in _models_from_rows(profile_rows):
        for pathway in pathways:
            for k in sorted({int(row["k"]) for row in profile_rows}):
                group = [
                    row
                    for row in profile_rows
                    if row["model"] == model
                    and row["pathway"] == pathway
                    and int(row["k"]) == k
                ]
                if not group:
                    continue
                rows.append(
                    {
                        "model": model,
                        "pathway": pathway,
                        "k": k,
                        "profile_count": len(group),
                        **{
                            metric: _rounded_mean(
                                [float(row[metric]) for row in group]
                            )
                            for metric in METRIC_NAMES
                        },
                    }
                )
    return rows
