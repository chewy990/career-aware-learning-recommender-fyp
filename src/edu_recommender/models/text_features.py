"""Own models text features responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.data import LearnerProfile, Resource


def _profile_document(profile: LearnerProfile, gaps: dict[str, float]) -> str:
    gap_text = " ".join(
        skill
        for skill, score in sorted(gaps.items())
        for _ in range(max(1, round(score * 3)))
    )
    return " ".join(
        [
            profile.target_pathway.replace("_", " "),
            " ".join(sorted(profile.current_skills)),
            " ".join(sorted(profile.completed_topics)),
            " ".join(sorted(profile.weak_skills)),
            gap_text,
            profile.preferred_format,
        ]
    )

def _resource_document(resource: Resource) -> str:
    return " ".join(
        [
            resource.title,
            resource.provider,
            resource.topic,
            " ".join(sorted(resource.skills)),
            " ".join(sorted(resource.prerequisites)),
            resource.format,
            resource.description,
        ]
    )
