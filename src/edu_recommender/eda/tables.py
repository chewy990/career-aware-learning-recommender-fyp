"""Own eda tables responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import itertools
import statistics
from collections import Counter

from edu_recommender.data import LearnerProfile, Resource

from .contracts import DIFFICULTY_LABELS, DURATION_BANDS, PATHWAY_ORDER


def build_eda_tables(
    resources: list[Resource],
    profiles: list[LearnerProfile],
    relevance: dict[str, set[str]],
    skill_map: dict[str, dict[str, int]],
    row_counts: dict[str, int],
) -> dict[str, list[dict[str, object]]]:
    """Build eda tables deterministically from the supplied evidence."""

    resource_count = len(resources)
    profile_count = len(profiles)
    profile_by_id = {profile.profile_id: profile for profile in profiles}

    tables: dict[str, list[dict[str, object]]] = {}
    dataset_purposes = {
        "resources.csv": "Learning-resource catalogue",
        "resource_modules.csv": "Verified module and source metadata",
        "skill_map.csv": "Pathway skill requirements",
        "learner_profiles.csv": "Fixed evaluation profiles",
        "relevance_judgements.csv": "Curated evaluation labels",
        "skill_sources.csv": "Skill-map evidence sources",
    }
    tables["dataset_summary.csv"] = [
        {
            "dataset": name,
            "row_count": row_counts[name],
            "purpose": dataset_purposes[name],
        }
        for name in dataset_purposes
    ]

    resource_distribution: list[dict[str, object]] = []
    _append_distribution(
        resource_distribution,
        "provider",
        Counter(resource.provider for resource in resources),
        resource_count,
    )
    _append_distribution(
        resource_distribution,
        "format",
        Counter(resource.format for resource in resources),
        resource_count,
    )
    _append_distribution(
        resource_distribution,
        "difficulty",
        Counter(DIFFICULTY_LABELS[resource.difficulty_level] for resource in resources),
        resource_count,
        category_order=("Beginner", "Intermediate", "Advanced"),
    )
    _append_distribution(
        resource_distribution,
        "duration_band",
        Counter(_duration_band(resource.duration_hours) for resource in resources),
        resource_count,
        category_order=tuple(band[0] for band in DURATION_BANDS),
    )
    _append_distribution(
        resource_distribution,
        "cost",
        Counter(resource.cost for resource in resources),
        resource_count,
    )
    for pathway in PATHWAY_ORDER:
        positive_count = sum(
            resource.pathway_relevance[pathway] > 0 for resource in resources
        )
        core_count = sum(
            resource.pathway_relevance[pathway] == 3 for resource in resources
        )
        resource_distribution.extend(
            [
                _distribution_row(
                    "pathway_positive_relevance",
                    pathway,
                    positive_count,
                    resource_count,
                ),
                _distribution_row(
                    "pathway_core_relevance",
                    pathway,
                    core_count,
                    resource_count,
                ),
            ]
        )
    tables["resource_distribution.csv"] = resource_distribution

    skill_counts = Counter(
        skill for resource in resources for skill in resource.skills
    )
    tables["skill_frequency.csv"] = [
        {
            "skill": skill,
            "resource_count": skill_counts[skill],
            "catalogue_percentage": _percentage(skill_counts[skill], resource_count),
            "mean_difficulty": round(
                statistics.mean(
                    resource.difficulty_level
                    for resource in resources
                    if skill in resource.skills
                ),
                2,
            ),
        }
        for skill in sorted(skill_counts, key=lambda item: (-skill_counts[item], item))
    ]

    pair_counts = Counter(
        pair
        for resource in resources
        for pair in itertools.combinations(sorted(resource.skills), 2)
    )
    tables["skill_cooccurrence.csv"] = [
        {
            "skill_a": pair[0],
            "skill_b": pair[1],
            "resource_count": count,
            "catalogue_percentage": _percentage(count, resource_count),
        }
        for pair, count in sorted(
            pair_counts.items(),
            key=lambda item: (-item[1], item[0][0], item[0][1]),
        )
    ]

    pathway_skill_coverage: list[dict[str, object]] = []
    for pathway in PATHWAY_ORDER:
        pathway_resources = [
            resource
            for resource in resources
            if resource.pathway_relevance[pathway] > 0
        ]
        for skill, required_level in sorted(skill_map[pathway].items()):
            if required_level == 0:
                continue
            coverage_count = sum(
                skill in resource.skills for resource in pathway_resources
            )
            pathway_skill_coverage.append(
                {
                    "pathway": pathway,
                    "skill": skill,
                    "required_level": required_level,
                    "pathway_relevant_resources": len(pathway_resources),
                    "resources_covering_skill": coverage_count,
                    "coverage_percentage": _percentage(
                        coverage_count, len(pathway_resources)
                    ),
                    "coverage_status": _coverage_status(coverage_count),
                }
            )
    tables["pathway_skill_coverage.csv"] = pathway_skill_coverage

    tables["profile_summary.csv"] = [
        {
            "profile_id": profile.profile_id,
            "target_pathway": profile.target_pathway,
            "preferred_difficulty": profile.preferred_difficulty,
            "max_duration_hours": profile.max_duration_hours,
            "preferred_format": profile.preferred_format,
            "current_skill_count": len(profile.current_skills),
            "weak_skill_count": len(profile.weak_skills),
            "completed_topic_count": len(profile.completed_topics),
        }
        for profile in sorted(profiles, key=lambda item: item.profile_id)
    ]

    profile_distribution: list[dict[str, object]] = []
    _append_distribution(
        profile_distribution,
        "target_pathway",
        Counter(profile.target_pathway for profile in profiles),
        profile_count,
        category_order=PATHWAY_ORDER,
    )
    _append_distribution(
        profile_distribution,
        "preferred_difficulty",
        Counter(
            DIFFICULTY_LABELS[profile.preferred_difficulty] for profile in profiles
        ),
        profile_count,
        category_order=("Beginner", "Intermediate", "Advanced"),
    )
    _append_distribution(
        profile_distribution,
        "preferred_format",
        Counter(profile.preferred_format for profile in profiles),
        profile_count,
    )
    tables["profile_distribution.csv"] = profile_distribution

    tables["relevance_summary.csv"] = [
        {
            "profile_id": profile_id,
            "target_pathway": profile_by_id[profile_id].target_pathway,
            "relevant_count": len(relevant_ids),
            "non_relevant_count": resource_count - len(relevant_ids),
            "relevance_prevalence": _percentage(
                len(relevant_ids), resource_count
            ),
        }
        for profile_id, relevant_ids in sorted(relevance.items())
    ]
    return tables

def _append_distribution(
    target: list[dict[str, object]],
    dimension: str,
    counts: Counter[str],
    total: int,
    category_order: tuple[str, ...] | None = None,
) -> None:
    if category_order is None:
        categories = sorted(counts, key=lambda item: (-counts[item], item))
    else:
        categories = [category for category in category_order if category in counts]
    target.extend(
        _distribution_row(dimension, category, counts[category], total)
        for category in categories
    )

def _distribution_row(
    dimension: str,
    category: str,
    count: int,
    total: int,
) -> dict[str, object]:
    return {
        "dimension": dimension,
        "category": category,
        "count": count,
        "percentage": _percentage(count, total),
    }

def _dimension_rows(
    rows: list[dict[str, object]],
    dimension: str,
) -> list[dict[str, object]]:
    return [row for row in rows if row["dimension"] == dimension]

def _duration_band(duration: float) -> str:
    for label, lower, upper in DURATION_BANDS:
        if lower == 0 and duration <= upper:
            return label
        if lower < duration <= upper:
            return label
    raise ValueError(f"Duration {duration} does not match a configured band")

def _coverage_status(count: int) -> str:
    if count == 0:
        return "no_coverage"
    if count < 3:
        return "limited"
    return "available"

def _percentage(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(100 * numerator / denominator, 1)

def _label(value: str) -> str:
    overrides = {
        "apis": "APIs",
        "ml_engineer": "Machine Learning Engineer",
        "oop": "OOP",
        "sql": "SQL",
    }
    return overrides.get(value, value.replace("_", " ").title())

def _chart_label(value: str) -> str:
    if any(character.isupper() for character in value):
        return value
    return _label(value)
