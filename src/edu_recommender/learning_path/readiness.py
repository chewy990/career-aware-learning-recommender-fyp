"""Own learning path readiness responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.presentation import display_skill


def stage_skill_cap(stage: str | None) -> int | None:
    """Return stage skill cap for the supplied learner and resource evidence."""

    if not stage:
        return None
    if stage.startswith("1."):
        return 1
    if stage.startswith("2."):
        return 2
    if stage.startswith("3."):
        return 3
    if stage.startswith("Optional"):
        return 2
    return None

def skill_completion_cap(
    stage: str | None,
    current_level: int,
    skill: str,
    skill_targets: dict[str, int] | None = None,
) -> int:
    """Return skill completion cap for the supplied learner and resource evidence."""

    target_level = (skill_targets or {}).get(skill, 3)
    if target_level <= 0:
        return current_level
    stage_cap = stage_skill_cap(stage)
    if stage_cap is None:
        return target_level
    return min(target_level, max(stage_cap, current_level + 1))

def completion_readiness(stage: str, current_skills: dict[str, int], item_skills: set[str]) -> tuple[bool, str]:
    """Return completion readiness for the supplied learner and resource evidence."""

    levels = [current_skills.get(skill, 0) for skill in item_skills]
    if stage.startswith("1."):
        return True, ""
    if stage.startswith("2."):
        if any(level >= 1 for level in levels):
            return True, ""
        return False, unlock_message(stage, current_skills, item_skills)
    if stage.startswith("3."):
        if any(level >= 2 for level in levels):
            return True, ""
        return False, unlock_message(stage, current_skills, item_skills)
    if stage.startswith("Optional"):
        if any(level >= 1 for level in levels):
            return True, ""
        return False, unlock_message(stage, current_skills, item_skills)
    return True, ""

def unlock_message(stage: str, current_skills: dict[str, int], item_skills: set[str]) -> str:
    """Return unlock message for the supplied learner and resource evidence."""

    if stage.startswith("3."):
        needed_level = 2
        course_type = "practice"
    else:
        needed_level = 1
        course_type = "foundation"
    needed_skills = [
        skill for skill in sorted(item_skills)
        if current_skills.get(skill, 0) < needed_level
    ]
    if not needed_skills:
        return "Unlock requirement: complete more foundation courses first."
    skill_text = unlock_skill_text(needed_skills[:2])
    if len(needed_skills) > 2:
        skill_text = f"{skill_text} or a related skill"
    return f"Unlock requirement: complete a {skill_text} {course_type} course first."

def unlock_skill_text(skills: list[str]) -> str:
    """Return unlock skill text for the supplied learner and resource evidence."""

    labels = [display_skill(skill) for skill in skills]
    if len(labels) == 1:
        return labels[0]
    return " or ".join(labels)

def can_improve_in_stage(stage: str, current_skills: dict[str, int], item_skills: set[str]) -> bool:
    """Return whether improve in stage."""

    max_level = stage_skill_cap(stage)
    if max_level is None:
        return True
    return any(current_skills.get(skill, 0) < max_level for skill in item_skills)

def can_gain_tracked_skill(
    stage: str,
    current_skills: dict[str, int],
    item_skills: set[str],
    skill_targets: dict[str, int],
) -> bool:
    """Return whether gain tracked skill."""

    return any(
        current_skills.get(skill, 0)
        < skill_completion_cap(stage, current_skills.get(skill, 0), skill, skill_targets)
        for skill in item_skills
    )
