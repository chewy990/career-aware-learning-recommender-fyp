"""Own prerequisite experiment diagnostics responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.models import (
    Recommendation,
    prerequisites_satisfied,
)

from .contracts import VARIANT_MODEL


def _validate_experiment(
    variant_recommendations: dict[str, list[Recommendation]],
    profiles: list[LearnerProfile],
    resources: list[Resource],
    recommendation_cutoff: int,
    diagnostic_rows: list[dict[str, object]],
) -> None:
    resource_lookup = {resource.resource_id: resource for resource in resources}
    for profile in profiles:
        recommendations = variant_recommendations[profile.profile_id]
        if len(recommendations) != recommendation_cutoff:
            raise ValueError(
                "Hard-prerequisite experiment cannot produce a full "
                f"top-{recommendation_cutoff} list for {profile.profile_id}."
            )
        invalid = [
            item.resource_id
            for item in recommendations
            if not prerequisites_satisfied(
                profile,
                resource_lookup[item.resource_id],
            )
        ]
        if invalid:
            raise ValueError(
                "Hard-prerequisite experiment returned ineligible resources "
                f"for {profile.profile_id}: {', '.join(invalid)}"
            )
    variant_diagnostic = next(
        row
        for row in diagnostic_rows
        if row["model"] == VARIANT_MODEL
    )
    if float(variant_diagnostic["prerequisite_validity_rate"]) != 1.0:
        raise ValueError(
            "Hard-prerequisite experiment did not reach 100% prerequisite "
            "validity at K=5."
        )
