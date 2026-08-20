"""Own statistical comparison label audit responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.models import Recommendation

from .contracts import AUDIT_ITEMS_PER_PATHWAY
from .reporting import _stable_sort_key


def build_label_audit_sample(
    hybrid_recommendations: dict[str, list[Recommendation]],
    profiles: list[LearnerProfile],
    resources: list[Resource],
    relevance_judgements: dict[str, set[str]],
    random_seed: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Build label audit sample deterministically from the supplied evidence."""

    profile_lookup = {profile.profile_id: profile for profile in profiles}
    resource_lookup = {resource.resource_id: resource for resource in resources}
    pathways = sorted({profile.target_pathway for profile in profiles})
    selected: list[tuple[str, str, str]] = []
    selected_pairs: set[tuple[str, str]] = set()
    category_targets = (
        "recommended_relevant",
        "recommended_not_relevant",
        "relevant_not_recommended",
        "not_relevant_not_recommended",
    )

    for pathway in pathways:
        pathway_profiles = sorted(
            (
                profile
                for profile in profiles
                if profile.target_pathway == pathway
            ),
            key=lambda profile: profile.profile_id,
        )
        candidates = {
            category: []
            for category in category_targets
        }
        for profile in pathway_profiles:
            top_ids = {
                item.resource_id
                for item in hybrid_recommendations[profile.profile_id][:10]
            }
            relevant = relevance_judgements[profile.profile_id]
            for resource in resources:
                pair = (profile.profile_id, resource.resource_id)
                if resource.resource_id in top_ids:
                    category = (
                        "recommended_relevant"
                        if resource.resource_id in relevant
                        else "recommended_not_relevant"
                    )
                else:
                    category = (
                        "relevant_not_recommended"
                        if resource.resource_id in relevant
                        else "not_relevant_not_recommended"
                    )
                candidates[category].append(pair)

        for category in category_targets:
            ordered = sorted(
                candidates[category],
                key=lambda pair: _stable_sort_key(
                    random_seed,
                    pathway,
                    category,
                    *pair,
                ),
            )
            for pair in ordered:
                if pair in selected_pairs:
                    continue
                selected.append((*pair, category))
                selected_pairs.add(pair)
                if sum(
                    item[2] == category
                    and profile_lookup[item[0]].target_pathway == pathway
                    for item in selected
                ) >= 2:
                    break

        pathway_count = sum(
            profile_lookup[profile_id].target_pathway == pathway
            for profile_id, _, _ in selected
        )
        if pathway_count < AUDIT_ITEMS_PER_PATHWAY:
            fallback = sorted(
                (
                    (profile.profile_id, resource.resource_id)
                    for profile in pathway_profiles
                    for resource in resources
                    if (profile.profile_id, resource.resource_id)
                    not in selected_pairs
                ),
                key=lambda pair: _stable_sort_key(
                    random_seed,
                    pathway,
                    "fallback",
                    *pair,
                ),
            )
            for pair in fallback[: AUDIT_ITEMS_PER_PATHWAY - pathway_count]:
                selected.append((*pair, "balanced_fallback"))
                selected_pairs.add(pair)

    blinded_rows: list[dict[str, object]] = []
    key_rows: list[dict[str, object]] = []
    for index, (profile_id, resource_id, reason) in enumerate(
        selected,
        start=1,
    ):
        profile = profile_lookup[profile_id]
        resource = resource_lookup[resource_id]
        audit_item_id = f"A{index:03d}"
        blinded_rows.append(
            {
                "audit_item_id": audit_item_id,
                "pathway": profile.target_pathway,
                "profile_name": profile.name,
                "target_pathway": profile.target_pathway,
                "current_skills": "; ".join(
                    f"{skill}:{level}"
                    for skill, level in sorted(
                        profile.current_skills.items()
                    )
                ),
                "weak_skills": "; ".join(sorted(profile.weak_skills)),
                "preferred_difficulty": profile.preferred_difficulty,
                "resource_title": resource.title,
                "provider": resource.provider,
                "topic": resource.topic,
                "skills": "; ".join(sorted(resource.skills)),
                "resource_difficulty": resource.difficulty_level,
                "format": resource.format,
                "prerequisites": "; ".join(
                    sorted(resource.prerequisites)
                ),
                "reviewer_relevance": "",
                "reviewer_confidence": "",
                "reviewer_notes": "",
            }
        )
        key_rows.append(
            {
                "audit_item_id": audit_item_id,
                "profile_id": profile_id,
                "resource_id": resource_id,
                "current_label": int(
                    resource_id in relevance_judgements[profile_id]
                ),
                "selection_reason": reason,
            }
        )
    return blinded_rows, key_rows
