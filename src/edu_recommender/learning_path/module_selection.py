"""Own learning path module selection responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.data import LearnerProfile, Resource, ResourceModule
from edu_recommender.presentation import display_skill_list


def modules_by_parent_resource(modules: list[ResourceModule]) -> dict[str, list[ResourceModule]]:
    """Return modules by parent resource for the supplied learner and resource evidence."""

    grouped: dict[str, list[ResourceModule]] = {}
    for module in modules:
        grouped.setdefault(module.parent_resource_id, []).append(module)
    return grouped

def selected_module_for_resource(
    profile: LearnerProfile,
    resource: Resource,
    modules: list[ResourceModule],
    gaps: dict[str, float],
) -> ResourceModule | None:
    """Return selected module for resource for the supplied learner and resource evidence."""

    if resource.format == "project":
        return None
    candidates = []
    for module in modules:
        matched_gap_score = sum(gaps.get(skill, 0.0) for skill in module.skills)
        if matched_gap_score <= 0:
            continue
        difficulty_fit = max(0.0, 1 - abs(module.difficulty_level - profile.preferred_difficulty) / 2)
        score = matched_gap_score + difficulty_fit
        candidates.append((score, module))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1].duration_hours, item[1].module_title))
    return candidates[0][1]

def resource_item_source(resource: Resource, module: ResourceModule | None) -> str:
    """Return resource item source for the supplied learner and resource evidence."""

    if module and module.source_url and module.date_checked:
        return f"From: {module.provider} - {module.module_title}"
    return resource_provider_source(resource)

def resource_provider_source(resource: Resource) -> str:
    """Return resource provider source for the supplied learner and resource evidence."""

    provider = resource.provider.strip()
    if not provider:
        return ""
    if resource.format in {"course", "career_track"}:
        return f"From: {provider}"
    return f"From: {provider} - {resource.title}"

def learning_item_reason(stage: str, item_skills: set[str]) -> str:
    """Return learning item reason for the supplied learner and resource evidence."""

    skills = display_skill_list(sorted(item_skills)[:3])
    if not skills:
        return ""
    if stage.startswith("2."):
        return f"Why: Practise {skills}."
    if stage.startswith("3."):
        return f"Why: Deepen {skills}."
    if stage.startswith("Optional"):
        return f"Why: Optional reinforcement for {skills}."
    return f"Why: Targets {skills}."

def module_style_resource_title(resource: Resource) -> str:
    """Return module style resource title for the supplied learner and resource evidence."""

    if resource.format != "module":
        return resource.title
    prefix = f"{resource.provider} Module "
    if resource.title.startswith(prefix):
        return resource.title.removeprefix(prefix)
    return resource.title.replace(" Module ", " ", 1)
