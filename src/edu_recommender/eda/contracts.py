"""Own eda contracts responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from dataclasses import dataclass

EDA_VERSION = 1

PATHWAY_ORDER = (
    "data_analyst",
    "data_scientist",
    "data_engineer",
    "ml_engineer",
    "software_developer",
)

DIFFICULTY_LABELS = {1: "Beginner", 2: "Intermediate", 3: "Advanced"}

DURATION_BANDS = (
    ("0-2 hours", 0.0, 2.0),
    (">2-5 hours", 2.0, 5.0),
    (">5-10 hours", 5.0, 10.0),
    (">10-20 hours", 10.0, 20.0),
    (">20 hours", 20.0, float("inf")),
)

FIGURE_FILES = (
    "figures/resources_by_pathway.png",
    "figures/resources_by_provider.png",
    "figures/resources_by_format.png",
    "figures/resources_by_difficulty.png",
    "figures/resource_duration_distribution.png",
    "figures/resources_by_cost.png",
    "figures/skill_frequency.png",
    "figures/skill_cooccurrence.png",
    "figures/pathway_skill_coverage.png",
    "figures/profiles_by_pathway.png",
    "figures/relevance_by_profile.png",
)

TABLE_FIELDS = {
    "dataset_summary.csv": ["dataset", "row_count", "purpose"],
    "resource_distribution.csv": ["dimension", "category", "count", "percentage"],
    "skill_frequency.csv": [
        "skill",
        "resource_count",
        "catalogue_percentage",
        "mean_difficulty",
    ],
    "skill_cooccurrence.csv": [
        "skill_a",
        "skill_b",
        "resource_count",
        "catalogue_percentage",
    ],
    "pathway_skill_coverage.csv": [
        "pathway",
        "skill",
        "required_level",
        "pathway_relevant_resources",
        "resources_covering_skill",
        "coverage_percentage",
        "coverage_status",
    ],
    "profile_summary.csv": [
        "profile_id",
        "target_pathway",
        "preferred_difficulty",
        "max_duration_hours",
        "preferred_format",
        "current_skill_count",
        "weak_skill_count",
        "completed_topic_count",
    ],
    "profile_distribution.csv": ["dimension", "category", "count", "percentage"],
    "relevance_summary.csv": [
        "profile_id",
        "target_pathway",
        "relevant_count",
        "non_relevant_count",
        "relevance_prevalence",
    ],
    "eda_findings.csv": ["figure", "title", "finding", "implication"],
}

@dataclass(frozen=True)
class EdaResult:
    """Record the tables, findings, and artifact paths produced by the EDA phase."""

    tables: dict[str, list[dict[str, object]]]
    findings: tuple[dict[str, str], ...]
    output_files: tuple[str, ...]
