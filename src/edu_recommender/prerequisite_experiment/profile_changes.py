"""Own prerequisite experiment profile changes responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.models import (
    Recommendation,
    prerequisites_satisfied,
)

from .contracts import BASELINE_MODEL, PRIMARY_K, VARIANT_MODEL


def build_profile_change_rows(
    baseline_recommendations: dict[str, list[Recommendation]],
    variant_recommendations: dict[str, list[Recommendation]],
    profiles: list[LearnerProfile],
    resources: list[Resource],
    relevance_judgements: dict[str, set[str]],
    profile_metric_rows: list[dict[str, object]],
    top_k: int,
) -> list[dict[str, object]]:
    """Build profile change rows deterministically from the supplied evidence."""

    profile_lookup = {profile.profile_id: profile for profile in profiles}
    resource_lookup = {resource.resource_id: resource for resource in resources}
    metric_lookup = {
        (
            str(row["model"]),
            str(row["profile_id"]),
            int(row["k"]),
        ): row
        for row in profile_metric_rows
    }
    rows: list[dict[str, object]] = []
    for profile_id in sorted(baseline_recommendations):
        profile = profile_lookup[profile_id]
        baseline_ids = [
            item.resource_id
            for item in baseline_recommendations[profile_id][:top_k]
        ]
        variant_ids = [
            item.resource_id
            for item in variant_recommendations[profile_id][:top_k]
        ]
        baseline_invalid = [
            resource_id
            for resource_id in baseline_ids
            if not prerequisites_satisfied(
                profile,
                resource_lookup[resource_id],
            )
        ]
        variant_invalid = [
            resource_id
            for resource_id in variant_ids
            if not prerequisites_satisfied(
                profile,
                resource_lookup[resource_id],
            )
        ]
        removed = [
            resource_id
            for resource_id in baseline_ids
            if resource_id not in variant_ids
        ]
        replacements = [
            resource_id
            for resource_id in variant_ids
            if resource_id not in baseline_ids
        ]
        baseline_ndcg = float(
            metric_lookup[(BASELINE_MODEL, profile_id, PRIMARY_K)][
                "ndcg_at_k"
            ]
        )
        variant_ndcg = float(
            metric_lookup[(VARIANT_MODEL, profile_id, PRIMARY_K)][
                "ndcg_at_k"
            ]
        )
        rows.append(
            {
                "profile_id": profile_id,
                "pathway": profile.target_pathway,
                "ranking_changed": baseline_ids != variant_ids,
                "top_5_changed": (
                    baseline_ids[:PRIMARY_K] != variant_ids[:PRIMARY_K]
                ),
                "top_10_overlap": round(
                    len(set(baseline_ids) & set(variant_ids)) / top_k,
                    4,
                ),
                "baseline_invalid_at_5_count": sum(
                    resource_id in baseline_invalid
                    for resource_id in baseline_ids[:PRIMARY_K]
                ),
                "variant_invalid_at_5_count": sum(
                    resource_id in variant_invalid
                    for resource_id in variant_ids[:PRIMARY_K]
                ),
                "baseline_invalid_count": len(baseline_invalid),
                "variant_invalid_count": len(variant_invalid),
                "baseline_invalid_ids": ";".join(baseline_invalid),
                "removed_ids": ";".join(removed),
                "replacement_ids": ";".join(replacements),
                "relevant_replacement_count": sum(
                    resource_id in relevance_judgements[profile_id]
                    for resource_id in replacements
                ),
                "baseline_ndcg_at_5": round(baseline_ndcg, 6),
                "variant_ndcg_at_5": round(variant_ndcg, 6),
                "ndcg_at_5_difference": round(
                    variant_ndcg - baseline_ndcg,
                    6,
                ),
                "baseline_top_5": ";".join(baseline_ids[:PRIMARY_K]),
                "variant_top_5": ";".join(variant_ids[:PRIMARY_K]),
            }
        )
    return rows
