"""Own learning path construction responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.models import Recommendation, RecommenderSuite
from edu_recommender.presentation import display_skill_list


def build_learning_path(
    suite: RecommenderSuite,
    profile: LearnerProfile,
    resources_by_id: dict[str, Resource],
    total_k: int,
) -> dict[str, list[Recommendation]]:
    """Build learning path deterministically from the supplied evidence."""

    recommendations = suite.recommend(profile, model="hybrid", top_k=total_k, include_broad_tracks=False)
    gaps = suite.skill_gaps(profile)
    stages: dict[str, list[Recommendation]] = {
        "1. Learn just enough": [],
        "2. Start a practical project": project_recommendations_for_profile(
            profile, resources_by_id, gaps, limit=3
        ),
        "3. Deepen later": deepen_recommendations_for_profile(
            profile, resources_by_id, gaps, limit=3
        ),
        "Optional structured tracks": structured_tracks_for_profile(profile, resources_by_id, gaps, limit=3),
    }
    project_ids = {recommendation.resource_id for recommendation in stages["2. Start a practical project"]}
    deepen_ids = {recommendation.resource_id for recommendation in stages["3. Deepen later"]}

    for recommendation in recommendations:
        resource = resources_by_id[recommendation.resource_id]
        if (
            is_broad_track(resource)
            or recommendation.resource_id in project_ids
            or recommendation.resource_id in deepen_ids
        ):
            continue
        matched_gap_strength = max((gaps.get(skill, 0.0) for skill in resource.skills), default=0.0)
        if resource.format == "project":
            stages["2. Start a practical project"].append(recommendation)
        elif matched_gap_strength >= 0.7 or resource.difficulty_level <= profile.preferred_difficulty:
            stages["1. Learn just enough"].append(recommendation)

    return balance_path_stages(stages)

def balance_path_stages(stages: dict[str, list[Recommendation]]) -> dict[str, list[Recommendation]]:
    """Return balance path stages for the supplied learner and resource evidence."""

    return {stage: list(recommendations[:4]) for stage, recommendations in stages.items()}

def project_recommendations_for_profile(
    profile: LearnerProfile,
    resources_by_id: dict[str, Resource],
    gaps: dict[str, float],
    limit: int,
) -> list[Recommendation]:
    """Return project recommendations for profile for the supplied learner and resource evidence."""

    scored = []
    for resource in resources_by_id.values():
        if resource.format != "project":
            continue
        if is_broad_track(resource) or is_supporting_resource(resource):
            continue
        skill_gap_match = sum(gaps.get(skill, 0.0) for skill in resource.skills)
        pathway_relevance = resource.pathway_relevance.get(profile.target_pathway, 0)
        if pathway_relevance == 0:
            continue
        difficulty_fit = max(0.0, 1 - abs(resource.difficulty_level - profile.preferred_difficulty) / 2)
        prerequisite_fit = project_prerequisite_fit(profile, resource)
        score = skill_gap_match + pathway_relevance + difficulty_fit + prerequisite_fit
        if score > 0:
            scored.append((score, resource))

    scored.sort(key=lambda item: (-item[0], item[1].duration_hours, item[1].title))
    return [
        Recommendation(
            profile_id=profile.profile_id,
            model="project_selector",
            rank=index + 1,
            resource_id=resource.resource_id,
            title=resource.title,
            provider=resource.provider,
            score=round(score, 4),
            explanation=f"Practise {display_skill_list(sorted(resource.skills)[:3])}.",
        )
        for index, (score, resource) in enumerate(scored[:limit])
    ]

def deepen_recommendations_for_profile(
    profile: LearnerProfile,
    resources_by_id: dict[str, Resource],
    gaps: dict[str, float],
    limit: int,
) -> list[Recommendation]:
    """Return deepen recommendations for profile for the supplied learner and resource evidence."""

    scored = []
    for resource in resources_by_id.values():
        if resource.format in {"project", "career_track"} or is_broad_track(resource) or is_supporting_resource(resource):
            continue
        pathway_relevance = resource.pathway_relevance.get(profile.target_pathway, 0)
        if pathway_relevance == 0:
            continue
        skill_gap_match = sum(gaps.get(skill, 0.0) for skill in resource.skills)
        depth_bonus = 1.0 if resource.difficulty_level > profile.preferred_difficulty else 0.35
        prerequisite_fit = project_prerequisite_fit(profile, resource)
        score = skill_gap_match + pathway_relevance + depth_bonus + prerequisite_fit
        if score > 0:
            scored.append((score, resource))

    scored.sort(key=lambda item: (-item[0], item[1].duration_hours, item[1].title))
    return [
        Recommendation(
            profile_id=profile.profile_id,
            model="deepen_selector",
            rank=index + 1,
            resource_id=resource.resource_id,
            title=resource.title,
            provider=resource.provider,
            score=round(score, 4),
            explanation=f"Deepen {display_skill_list(sorted(resource.skills)[:3])}.",
        )
        for index, (score, resource) in enumerate(scored[:limit])
    ]

def project_prerequisite_fit(profile: LearnerProfile, resource: Resource) -> float:
    """Return project prerequisite fit for the supplied learner and resource evidence."""

    if not resource.prerequisites:
        return 1.0
    met = {
        prerequisite
        for prerequisite in resource.prerequisites
        if prerequisite in profile.completed_topics or profile.current_skills.get(prerequisite, 0) >= 1
    }
    return len(met) / len(resource.prerequisites)

def structured_tracks_for_profile(
    profile: LearnerProfile,
    resources_by_id: dict[str, Resource],
    gaps: dict[str, float],
    limit: int,
) -> list[Recommendation]:
    """Return structured tracks for profile for the supplied learner and resource evidence."""

    scored = []
    for resource in resources_by_id.values():
        if not is_broad_track(resource):
            continue
        if is_supporting_resource(resource):
            continue
        if resource.pathway_relevance.get(profile.target_pathway, 0) == 0:
            continue
        skill_gap_match = sum(gaps.get(skill, 0.0) for skill in resource.skills)
        score = resource.pathway_relevance.get(profile.target_pathway, 0) + skill_gap_match
        if score > 0:
            scored.append((score, resource))
    scored.sort(key=lambda item: (-item[0], item[1].duration_hours, item[1].title))
    return [
        Recommendation(
            profile_id=profile.profile_id,
            model="optional_track",
            rank=index + 1,
            resource_id=resource.resource_id,
            title=resource.title,
            provider=resource.provider,
            score=round(score, 4),
            explanation=f"Optional reinforcement for {display_skill_list(sorted(resource.skills)[:3])}.",
        )
        for index, (score, resource) in enumerate(scored[:limit])
    ]

def is_broad_track(resource: Resource) -> bool:
    """Return whether broad track."""

    return resource.format == "career_track" or resource.duration_hours >= 20

def is_supporting_resource(resource: Resource) -> bool:
    """Return whether supporting resource."""

    return resource.format in {"article", "reading", "youtube", "video_essay", "explainer"}
