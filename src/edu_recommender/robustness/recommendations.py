"""Own robustness recommendations responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from statistics import mean

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.evaluation import (
    build_metric_summary_rows,
    build_profile_metric_rows,
)
from edu_recommender.models import (
    Recommendation,
    RecommenderSuite,
)


def _recommend_with_weights(
    resources: list[Resource],
    skill_map: dict[str, dict[str, int]],
    profiles: list[LearnerProfile],
    weights: dict[str, float],
    cutoff: int,
) -> dict[str, list[Recommendation]]:
    suite = RecommenderSuite(
        resources,
        skill_map,
        hybrid_weights=weights,
    )
    return {
        profile.profile_id: suite.recommend(
            profile,
            model="hybrid",
            top_k=cutoff,
        )
        for profile in profiles
    }

def _baseline_summary(
    baseline: dict[str, list[Recommendation]],
    profiles: list[LearnerProfile],
    relevance: dict[str, set[str]],
    k_values: tuple[int, ...],
) -> dict[int, dict[str, object]]:
    rows = build_metric_summary_rows(
        build_profile_metric_rows(
            {"hybrid": baseline},
            relevance,
            profiles,
            k_values,
        )
    )
    return {int(row["k"]): row for row in rows}

def _ranking_stability(
    baseline: dict[str, list[Recommendation]],
    comparison: dict[str, list[Recommendation]],
    k: int,
) -> tuple[float, int]:
    overlaps: list[float] = []
    changed = 0
    for profile_id in sorted(baseline):
        baseline_ids = [
            item.resource_id
            for item in baseline[profile_id][:k]
        ]
        comparison_ids = [
            item.resource_id
            for item in comparison[profile_id][:k]
        ]
        overlaps.append(
            len(set(baseline_ids) & set(comparison_ids)) / k
        )
        if baseline_ids != comparison_ids:
            changed += 1
    return round(mean(overlaps), 4), changed

def _assert_same_rankings(
    expected: dict[str, list[Recommendation]],
    actual: dict[str, list[Recommendation]],
) -> None:
    for profile_id, expected_recommendations in expected.items():
        expected_ids = [
            item.resource_id
            for item in expected_recommendations
        ]
        actual_ids = [
            item.resource_id
            for item in actual[profile_id]
        ]
        if expected_ids != actual_ids:
            raise RuntimeError(
                "Explicit baseline hybrid weights changed the default ranking "
                f"for {profile_id}."
            )
