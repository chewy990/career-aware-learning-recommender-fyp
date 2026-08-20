"""Own validation contracts responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PATHWAYS = (
    "data_analyst",
    "ml_engineer",
    "software_developer",
    "data_scientist",
    "data_engineer",
)

RESOURCE_FORMATS = {
    "article",
    "career_track",
    "course",
    "module",
    "project",
    "reading",
    "tutorial",
    "video",
    "video_essay",
    "youtube",
}

RESOURCE_TOPICS = {
    "apis",
    "career_path",
    "dashboards",
    "data_analysis",
    "data_analytics",
    "data_cleaning",
    "data_visualisation",
    "databases",
    "deployment",
    "excel",
    "machine_learning",
    "model_evaluation",
    "oop",
    "programming",
    "project",
    "python",
    "recommender_systems",
    "sql",
    "statistics",
    "testing",
    "version_control",
}

RESOURCE_COSTS = {"free", "paid"}

SOURCE_TYPES = {
    "career_skills_source",
    "design_decision",
    "learning_platform",
    "project_document",
}

RESOURCE_COLUMNS = (
    "resource_id",
    "title",
    "provider",
    "topic",
    "skills",
    "difficulty_level",
    "duration_hours",
    "format",
    "prerequisites",
    "cost",
    "popularity_score",
    "quality_score",
    *(f"{pathway}_relevance" for pathway in PATHWAYS),
    "description",
    "source_url",
    "date_checked",
)

MODULE_COLUMNS = (
    "module_id",
    "parent_resource_id",
    "module_title",
    "provider",
    "skills",
    "difficulty_level",
    "duration_hours",
    "source_url",
    "date_checked",
)

SKILL_MAP_COLUMNS = ("skill", *PATHWAYS)

PROFILE_COLUMNS = (
    "profile_id",
    "name",
    "target_pathway",
    "current_skills",
    "completed_topics",
    "weak_skills",
    "preferred_difficulty",
    "max_duration_hours",
    "preferred_format",
)

JUDGEMENT_COLUMNS = ("profile_id", "relevant_resource_ids")

GRADED_JUDGEMENT_COLUMNS = (
    "profile_id",
    "resource_id",
    "relevance_grade",
)

SOURCE_COLUMNS = (
    "source_id",
    "source_name",
    "source_type",
    "url",
    "pathways_supported",
    "skills_supported",
    "evidence_summary",
)

@dataclass(frozen=True)
class ValidationIssue:
    """Describe one actionable data validation failure."""

    dataset: str
    row: int | None
    column: str | None
    message: str

    def format(self) -> str:
        location = self.dataset
        if self.row is not None:
            location += f":row {self.row}"
        if self.column:
            location += f" [{self.column}]"
        return f"{location}: {self.message}"

class DataValidationError(ValueError):
    """Report all validation failures together so pipeline errors remain actionable."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = tuple(issues)
        detail = "\n".join(f"- {issue.format()}" for issue in self.issues)
        super().__init__(
            f"Data validation failed with {len(self.issues)} issue(s):\n{detail}"
        )

@dataclass(frozen=True)
class ValidationSummary:
    """Record validated dataset sizes and a deterministic data fingerprint."""

    row_counts: dict[str, int]
    checks: tuple[dict[str, str], ...]

    def as_rows(self) -> list[dict[str, str]]:
        return [dict(row) for row in self.checks]

@dataclass(frozen=True)
class _Table:
    name: str
    path: Path
    headers: list[str]
    rows: list[dict[str, str]]


_SPECS = {
    "resources.csv": (RESOURCE_COLUMNS, "resource_id", re.compile(r"R\d{3}")),
    "resource_modules.csv": (MODULE_COLUMNS, "module_id", re.compile(r"M\d{3}")),
    "skill_map.csv": (
        SKILL_MAP_COLUMNS,
        "skill",
        re.compile(r"[a-z][a-z0-9_]*"),
    ),
    "learner_profiles.csv": (PROFILE_COLUMNS, "profile_id", re.compile(r"P\d{3}")),
    "relevance_judgements.csv": (
        JUDGEMENT_COLUMNS,
        "profile_id",
        re.compile(r"P\d{3}"),
    ),
    "skill_sources.csv": (SOURCE_COLUMNS, "source_id", re.compile(r"S\d{3}")),
}
