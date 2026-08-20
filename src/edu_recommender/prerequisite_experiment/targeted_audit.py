"""Own prerequisite experiment targeted audit responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import hashlib

from edu_recommender.data import LearnerProfile, Resource


def build_targeted_audit(
    profile_change_rows: list[dict[str, object]],
    profiles: list[LearnerProfile],
    resources: list[Resource],
    relevance_judgements: dict[str, set[str]],
    random_seed: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Build targeted audit deterministically from the supplied evidence."""

    profile_lookup = {profile.profile_id: profile for profile in profiles}
    resource_lookup = {resource.resource_id: resource for resource in resources}
    candidates: list[tuple[str, str, str]] = []
    for row in profile_change_rows:
        if not bool(row["top_5_changed"]):
            continue
        profile_id = str(row["profile_id"])
        baseline_ids = set(str(row["baseline_top_5"]).split(";"))
        variant_ids = set(str(row["variant_top_5"]).split(";"))
        candidates.extend(
            (profile_id, resource_id, "baseline_removed")
            for resource_id in baseline_ids - variant_ids
        )
        candidates.extend(
            (profile_id, resource_id, "variant_replacement")
            for resource_id in variant_ids - baseline_ids
        )
    candidates.sort(
        key=lambda item: hashlib.sha256(
            (
                f"{random_seed}:prerequisite_audit:"
                f"{item[0]}:{item[1]}:{item[2]}"
            ).encode()
        ).hexdigest()
    )

    blinded_rows: list[dict[str, object]] = []
    key_rows: list[dict[str, object]] = []
    for index, (profile_id, resource_id, role) in enumerate(
        candidates,
        start=1,
    ):
        profile = profile_lookup[profile_id]
        resource = resource_lookup[resource_id]
        audit_item_id = f"H{index:03d}"
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
                "experiment_role": role,
            }
        )
    return blinded_rows, key_rows
