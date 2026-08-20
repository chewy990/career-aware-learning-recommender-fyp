"""Own evaluation diagnostics responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from statistics import mean

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.models import Recommendation

from .reporting import _ordered_models, _rounded_mean, _validate_k_values


def build_diagnostic_profile_rows(
    recommendations_by_model: dict[str, dict[str, list[Recommendation]]],
    profiles: list[LearnerProfile],
    resources: list[Resource],
    skill_gaps_by_profile: dict[str, dict[str, float]],
    k_values: tuple[int, ...],
) -> list[dict[str, object]]:
    """Build diagnostic profile rows deterministically from the supplied evidence."""

    _validate_k_values(k_values)
    profile_lookup = {profile.profile_id: profile for profile in profiles}
    resource_lookup = {resource.resource_id: resource for resource in resources}
    rows: list[dict[str, object]] = []
    for model in _ordered_models(recommendations_by_model):
        for profile_id in sorted(recommendations_by_model[model]):
            profile = profile_lookup[profile_id]
            for k in k_values:
                selected = [
                    resource_lookup[item.resource_id]
                    for item in recommendations_by_model[model][profile_id][:k]
                ]
                count = len(selected)
                providers = {resource.provider for resource in selected}
                formats = {resource.format for resource in selected}
                rows.append(
                    {
                        "model": model,
                        "profile_id": profile_id,
                        "pathway": profile.target_pathway,
                        "k": k,
                        "recommended_count": count,
                        "distinct_provider_count": len(providers),
                        "provider_diversity": round(
                            len(providers) / count if count else 0.0,
                            6,
                        ),
                        "distinct_format_count": len(formats),
                        "format_diversity": round(
                            len(formats) / count if count else 0.0,
                            6,
                        ),
                        "skill_gap_coverage": round(
                            skill_gap_coverage(
                                selected,
                                skill_gaps_by_profile[profile_id],
                            ),
                            6,
                        ),
                        "intra_list_diversity": round(
                            intra_list_diversity(selected),
                            6,
                        ),
                        "difficulty_match_rate": round(
                            difficulty_match_rate(selected, profile),
                            6,
                        ),
                        "prerequisite_validity_rate": round(
                            prerequisite_validity_rate(selected, profile),
                            6,
                        ),
                    }
                )
    return rows

def build_diagnostic_summary_rows(
    diagnostic_profile_rows: list[dict[str, object]],
    recommendations_by_model: dict[str, dict[str, list[Recommendation]]],
    resources: list[Resource],
    k_values: tuple[int, ...],
) -> list[dict[str, object]]:
    """Build diagnostic summary rows deterministically from the supplied evidence."""

    catalogue_size = len(resources)
    resource_lookup = {resource.resource_id: resource for resource in resources}
    rows: list[dict[str, object]] = []
    mean_fields = (
        "provider_diversity",
        "format_diversity",
        "skill_gap_coverage",
        "intra_list_diversity",
        "difficulty_match_rate",
        "prerequisite_validity_rate",
    )
    for model in _ordered_models(recommendations_by_model):
        for k in k_values:
            group = [
                row
                for row in diagnostic_profile_rows
                if row["model"] == model and int(row["k"]) == k
            ]
            selected_ids = {
                recommendation.resource_id
                for recommendations in recommendations_by_model[model].values()
                for recommendation in recommendations[:k]
            }
            rows.append(
                {
                    "model": model,
                    "k": k,
                    "profile_count": len(group),
                    "unique_resources_recommended": len(selected_ids),
                    "catalogue_size": catalogue_size,
                    "catalogue_coverage": round(
                        len(selected_ids) / catalogue_size
                        if catalogue_size
                        else 0.0,
                        4,
                    ),
                    "provider_exposure_count": len(
                        {
                            recommendation.provider
                            for recommendations in recommendations_by_model[
                                model
                            ].values()
                            for recommendation in recommendations[:k]
                        }
                    ),
                    "format_exposure_count": len(
                        {
                            resource_lookup[recommendation.resource_id].format
                            for recommendations in recommendations_by_model[
                                model
                            ].values()
                            for recommendation in recommendations[:k]
                        }
                    ),
                    **{
                        field: _rounded_mean(
                            [float(row[field]) for row in group]
                        )
                        for field in mean_fields
                    },
                }
            )
    return rows

def skill_gap_coverage(
    resources: list[Resource],
    skill_gaps: dict[str, float],
) -> float:
    """Return the share of a learner's skill gaps represented in the recommendation list."""

    if not skill_gaps:
        return 1.0
    covered_skills = set().union(
        *(resource.skills for resource in resources)
    ) if resources else set()
    covered_weight = sum(
        weight
        for skill, weight in skill_gaps.items()
        if skill in covered_skills
    )
    return covered_weight / sum(skill_gaps.values())

def intra_list_diversity(resources: list[Resource]) -> float:
    """Return mean pairwise dissimilarity between recommended resource feature vectors."""

    if len(resources) < 2:
        return 0.0
    distances: list[float] = []
    for left_index, left in enumerate(resources):
        for right in resources[left_index + 1 :]:
            union = left.skills | right.skills
            similarity = len(left.skills & right.skills) / len(union) if union else 1.0
            distances.append(1 - similarity)
    return mean(distances) if distances else 0.0

def difficulty_match_rate(
    resources: list[Resource],
    profile: LearnerProfile,
) -> float:
    """Return the share of recommendations within the accepted learner difficulty band."""

    if not resources:
        return 0.0
    matches = sum(
        abs(resource.difficulty_level - profile.preferred_difficulty) <= 1
        for resource in resources
    )
    return matches / len(resources)

def prerequisite_validity_rate(
    resources: list[Resource],
    profile: LearnerProfile,
) -> float:
    """Return the share of recommendations whose prerequisites the learner satisfies."""

    if not resources:
        return 0.0
    valid = 0
    for resource in resources:
        if all(
            prerequisite in profile.completed_topics
            or profile.current_skills.get(prerequisite, 0) >= 1
            for prerequisite in resource.prerequisites
        ):
            valid += 1
    return valid / len(resources)
