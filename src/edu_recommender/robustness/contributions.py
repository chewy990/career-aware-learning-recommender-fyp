"""Own robustness contributions responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.models import (
    Recommendation,
    RecommenderSuite,
)

from .contracts import COMPONENTS


def _build_component_contribution_rows(
    resources: list[Resource],
    skill_map: dict[str, dict[str, int]],
    profiles: list[LearnerProfile],
    baseline: dict[str, list[Recommendation]],
    example_count: int,
) -> list[dict[str, object]]:
    suite = RecommenderSuite(resources, skill_map)
    profile_lookup = {profile.profile_id: profile for profile in profiles}
    resource_lookup = {resource.resource_id: resource for resource in resources}
    rows: list[dict[str, object]] = []
    for profile_id in sorted(baseline):
        profile = profile_lookup[profile_id]
        for recommendation in baseline[profile_id][:example_count]:
            resource = resource_lookup[recommendation.resource_id]
            details = suite.hybrid_score_details(profile, resource)
            rows.append(
                {
                    "profile_id": profile_id,
                    "pathway": profile.target_pathway,
                    "rank": recommendation.rank,
                    "resource_id": resource.resource_id,
                    "title": resource.title,
                    **{
                        f"raw_{component}": round(
                            details.raw_signals[component],
                            6,
                        )
                        for component in COMPONENTS
                    },
                    **{
                        f"contribution_{component}": round(
                            details.weighted_contributions[component],
                            6,
                        )
                        for component in COMPONENTS
                    },
                    "calculated_total_score": round(
                        details.total_score,
                        6,
                    ),
                    "pipeline_score": recommendation.score,
                }
            )
    return rows
