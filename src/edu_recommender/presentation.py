from __future__ import annotations

from collections.abc import Iterable

from edu_recommender.data import Resource, ResourceModule

PATHWAY_LABELS = {
    "data_analyst": "Data Analyst",
    "data_engineer": "Data Engineer",
    "data_scientist": "Data Scientist",
    "ml_engineer": "ML Engineer",
    "software_developer": "Software Developer",
}

SKILL_LABELS = {
    "apis": "APIs",
    "oop": "Object-oriented programming",
    "sql": "SQL",
    "data_visualisation": "Data visualisation",
    "data_cleaning": "Data cleaning",
    "machine_learning": "Machine learning",
    "model_evaluation": "Model evaluation",
    "version_control": "Version control",
    "dashboards": "Dashboarding",
}

DIFFICULTY_LABELS = {
    1: "Beginner",
    2: "Intermediate",
    3: "Advanced",
}

SKILL_LEVEL_LABELS = {
    0: "Not started",
    1: "Basic",
    2: "Working knowledge",
    3: "Confident",
}


def display_pathway(pathway: str) -> str:
    """Return a stable, human-readable pathway label."""
    return PATHWAY_LABELS.get(pathway, pathway.replace("_", " ").title())


def display_skill(skill: str) -> str:
    """Return a stable, human-readable skill label."""
    return SKILL_LABELS.get(skill, skill.replace("_", " ").title())


def display_skill_list(skills: Iterable[str]) -> str:
    """Format skills deterministically for explanations and UI text."""
    ordered = sorted(set(skills))
    if not ordered:
        return "None yet"
    return ", ".join(display_skill(skill) for skill in ordered)


def skill_level_label(level: int) -> str:
    """Translate the supported 0-3 skill scale into user-facing text."""
    numeric_level = int(level)
    return SKILL_LEVEL_LABELS.get(numeric_level, str(numeric_level))


def difficulty_label(level: int) -> str:
    """Translate the supported 1-3 difficulty scale into user-facing text."""
    numeric_level = int(level)
    return DIFFICULTY_LABELS.get(numeric_level, str(numeric_level))


def source_url_for_item(
    resource: Resource,
    module: ResourceModule | None,
) -> str:
    """Return only a verified, item-specific catalogue URL."""
    if module and module.source_url:
        return module.source_url
    return resource.source_url
