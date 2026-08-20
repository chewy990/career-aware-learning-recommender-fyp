"""Own models signals responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.data import LearnerProfile, Resource


def _weighted_overlap(resource_skills: set[str], gaps: dict[str, float]) -> float:
    if not gaps:
        return 0.0
    matched_gap_weight = sum(gaps[skill] for skill in resource_skills if skill in gaps)
    total_gap_weight = sum(gaps.values())
    return min(matched_gap_weight / total_gap_weight, 1.0)

def _job_skill_alignment(resource_skills: set[str], pathway_requirements: dict[str, int]) -> float:
    important_skills = {skill for skill, weight in pathway_requirements.items() if weight >= 2}
    if not important_skills:
        return 0.0
    return len(resource_skills & important_skills) / len(important_skills)

def _prerequisite_match(profile: LearnerProfile, resource: Resource) -> float:
    if not resource.prerequisites:
        return 1.0
    met_prerequisites = {
        skill
        for skill in resource.prerequisites
        if skill in profile.completed_topics or profile.current_skills.get(skill, 0) >= 1
    }
    return len(met_prerequisites) / len(resource.prerequisites)

def prerequisites_satisfied(
    profile: LearnerProfile,
    resource: Resource,
) -> bool:
    """Return whether the learner meets every declared prerequisite for a resource."""

    return all(
        prerequisite in profile.completed_topics
        or profile.current_skills.get(prerequisite, 0) >= 1
        for prerequisite in resource.prerequisites
    )

def _scope_fit(resource: Resource) -> float:
    if resource.format == "career_track":
        return 0.25
    if resource.duration_hours >= 30:
        return 0.30
    if resource.duration_hours >= 20:
        return 0.45
    if resource.duration_hours >= 12:
        return 0.70
    return 1.0

def _is_broad_track(resource: Resource) -> bool:
    return resource.format == "career_track" or resource.duration_hours >= 20

def _is_supporting_resource(resource: Resource) -> bool:
    return resource.format in {"article", "reading", "youtube", "video_essay", "explainer"}
