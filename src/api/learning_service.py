from __future__ import annotations

from collections.abc import Sequence

from fastapi import HTTPException

from api.schemas import LearningPathRequest
from edu_recommender.data import LearnerProfile, Resource, ResourceModule
from edu_recommender.learning_path import (
    can_improve_in_stage,
    completion_readiness,
    learning_item_reason,
    module_style_resource_title,
    resource_item_source,
    skill_completion_cap,
)
from edu_recommender.presentation import (
    difficulty_label,
    display_pathway,
    display_skill,
    skill_level_label,
    source_url_for_item,
)
from edu_recommender.progression import next_pathways


def validate_known_skills(
    skills: dict[str, int] | set[str] | list[str],
    skill_map: dict[str, dict[str, int]],
) -> None:
    """Reject skill identifiers that cannot affect any supported pathway."""
    known = {
        skill
        for pathway_targets in skill_map.values()
        for skill in pathway_targets
    }
    unknown = sorted(set(skills) - known)
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown skill identifier: {unknown[0]}",
        )


def make_profile(
    payload: LearningPathRequest,
    skill_map: dict[str, dict[str, int]],
) -> LearnerProfile:
    """Convert an API learning request into the core learner-profile contract."""

    if payload.target_pathway not in skill_map:
        raise HTTPException(status_code=404, detail="Unknown pathway")
    validate_known_skills(payload.current_skills, skill_map)

    targets = skill_map[payload.target_pathway]
    skills = {skill: int(payload.current_skills.get(skill, 0)) for skill in targets}
    for skill, level in payload.current_skills.items():
        skills.setdefault(skill, int(level))
    completed_topics = set(payload.completed_topics)
    weak_skills = {
        skill
        for skill, target in targets.items()
        if target > 0 and skills.get(skill, 0) < target
    }
    return LearnerProfile(
        profile_id=payload.profile_id,
        name=payload.name,
        target_pathway=payload.target_pathway,
        current_skills=skills,
        completed_topics=completed_topics,
        weak_skills=weak_skills,
        preferred_difficulty=payload.preferred_difficulty,
        # Retained only inside the historical evaluation-profile contract.
        # The active product no longer exposes a maximum-duration preference.
        max_duration_hours=10,
        preferred_format=payload.preferred_format,
    )


def item_payload(
    profile: LearnerProfile,
    stage: str,
    resource: Resource,
    module: ResourceModule | None,
    gaps: dict[str, float],
    completed_item_ids: set[str],
    skill_targets: dict[str, int],
    score: float | None = None,
    explanation: str | None = None,
) -> dict[str, object]:
    """Serialise a learning-path item without changing the public API schema."""

    item_id = (
        f"module:{module.module_id}" if module else f"resource:{resource.resource_id}"
    )
    item_title = (
        module.module_title if module else module_style_resource_title(resource)
    )
    item_skills = module.skills if module else resource.skills
    item_difficulty = module.difficulty_level if module else resource.difficulty_level
    item_duration = module.duration_hours if module else resource.duration_hours
    completed = item_id in completed_item_ids
    ready, locked_reason = completion_readiness(
        stage,
        profile.current_skills,
        item_skills,
    )

    skill_changes = []
    for skill in sorted(item_skills):
        before = profile.current_skills.get(skill, 0)
        after_cap = skill_completion_cap(
            stage,
            before,
            skill,
            skill_targets,
        )
        after = min(before + 1, after_cap) if before < after_cap else before
        if after != before:
            skill_changes.append(
                {
                    "skill": skill,
                    "label": display_skill(skill),
                    "before": before,
                    "after": after,
                    "before_label": skill_level_label(before),
                    "after_label": skill_level_label(after),
                }
            )

    default_reason = learning_item_reason(stage, item_skills)
    return {
        "item_id": item_id,
        "resource_id": resource.resource_id,
        "title": item_title,
        "provider": resource.provider,
        "topic": resource.topic,
        "skills": sorted(item_skills),
        "skill_labels": [display_skill(skill) for skill in sorted(item_skills)],
        "difficulty_level": item_difficulty,
        "difficulty_label": difficulty_label(item_difficulty),
        "duration_hours": item_duration,
        "format": resource.format,
        "source": resource_item_source(resource, module),
        "source_url": source_url_for_item(resource, module),
        "reason": default_reason,
        "score": score,
        "explanation": explanation or default_reason,
        "completed": completed,
        "ready": ready or completed,
        "locked_reason": "" if ready or completed else locked_reason,
        "skill_changes": skill_changes,
        "can_improve": can_improve_in_stage(
            stage,
            profile.current_skills,
            item_skills,
        ),
    }


def course_complete(visible_items: list[dict[str, object]]) -> bool:
    """Return whether every useful item in the generated course is complete."""

    actionable = [item for item in visible_items if item["can_improve"]]
    return bool(actionable) and all(item["completed"] for item in actionable)


def next_pathway_options(
    skill_map: dict[str, dict[str, int]],
    current_skills: dict[str, int],
    current_pathway: str,
    excluded_pathways: Sequence[str] = (),
    limit: int = 2,
) -> list[dict[str, object]]:
    """Return the pathways closest to the learner's current skills, with labels.

    Ordering and content come from the skill map, so no pair of pathways is
    privileged in code. Pathways the learner already holds or has completed are
    excluded, because offering one would lead to a course with nothing left to
    do. A completed course must also stay excluded even after it is removed.
    The result describes shared skill requirements and is not evidence that
    learners move between these roles.

    """

    options = next_pathways(
        skill_map,
        current_skills,
        exclude=(current_pathway, *excluded_pathways),
        limit=limit,
    )
    return [
        {
            "pathway": option["pathway"],
            "label": display_pathway(str(option["pathway"])),
            "coverage": round(float(option["coverage"]), 4),
            "remaining": [
                {
                    "skill": skill,
                    "label": display_skill(skill),
                    "levels": levels,
                }
                for skill, levels in dict(option["remaining"]).items()
            ],
        }
        for option in options
    ]
