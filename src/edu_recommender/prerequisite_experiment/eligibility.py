"""Own prerequisite experiment eligibility responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from dataclasses import replace

from edu_recommender.data import LearnerProfile
from edu_recommender.models import (
    Recommendation,
    RecommenderSuite,
)

from .contracts import BASELINE_MODEL, VARIANT_MODEL


def build_eligible_recommendations(
    suite: RecommenderSuite,
    profiles: list[LearnerProfile],
    top_k: int,
) -> dict[str, list[Recommendation]]:
    """Build eligible recommendations deterministically from the supplied evidence."""

    recommendations: dict[str, list[Recommendation]] = {}
    for profile in sorted(profiles, key=lambda item: item.profile_id):
        eligible = suite.recommend(
            profile,
            model=BASELINE_MODEL,
            top_k=top_k,
            enforce_prerequisites=True,
        )
        recommendations[profile.profile_id] = [
            replace(
                recommendation,
                model=VARIANT_MODEL,
                explanation=(
                    recommendation.explanation
                    + " Hard prerequisite eligibility was satisfied."
                ),
            )
            for recommendation in eligible
        ]
    return recommendations
