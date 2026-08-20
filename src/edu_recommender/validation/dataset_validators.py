"""Own validation dataset validators responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from .contracts import (
    PATHWAYS,
    RESOURCE_COSTS,
    RESOURCE_FORMATS,
    RESOURCE_TOPICS,
    ValidationIssue,
    _Table,
)
from .parsing import (
    _http_url,
    _iso_date,
    _known_tokens,
    _safe_float,
    _safe_int,
    _tokens,
)
from .schemas import _allowed, _number_in_range


def _validate_skill_map(table: _Table, issues: list[ValidationIssue]) -> None:
    for row_number, row in enumerate(table.rows, start=2):
        for pathway in PATHWAYS:
            _number_in_range(
                table.name,
                row_number,
                pathway,
                row[pathway],
                0,
                3,
                issues,
                integer=True,
            )
    for pathway in PATHWAYS:
        if not any(_safe_int(row[pathway]) and _safe_int(row[pathway]) > 0 for row in table.rows):
            issues.append(
                ValidationIssue(
                    table.name,
                    None,
                    pathway,
                    "pathway must have at least one skill with a positive requirement",
                )
            )

def _validate_resources(
    table: _Table,
    canonical_skills: set[str],
    issues: list[ValidationIssue],
) -> None:
    for row_number, row in enumerate(table.rows, start=2):
        _allowed(table.name, row_number, "topic", row["topic"], RESOURCE_TOPICS, issues)
        _allowed(table.name, row_number, "format", row["format"], RESOURCE_FORMATS, issues)
        _allowed(table.name, row_number, "cost", row["cost"], RESOURCE_COSTS, issues)
        _number_in_range(
            table.name,
            row_number,
            "difficulty_level",
            row["difficulty_level"],
            1,
            3,
            issues,
            integer=True,
        )
        duration = _number_in_range(
            table.name, row_number, "duration_hours", row["duration_hours"], 0, 1000, issues
        )
        if duration is not None and duration == 0:
            issues.append(
                ValidationIssue(
                    table.name, row_number, "duration_hours", "must be greater than 0"
                )
            )
        _number_in_range(
            table.name, row_number, "popularity_score", row["popularity_score"], 0, 1, issues
        )
        _number_in_range(
            table.name, row_number, "quality_score", row["quality_score"], 0, 1, issues
        )
        for pathway in PATHWAYS:
            _number_in_range(
                table.name,
                row_number,
                f"{pathway}_relevance",
                row[f"{pathway}_relevance"],
                0,
                3,
                issues,
                integer=True,
            )
        skills = _tokens(table, row_number, "skills", row["skills"], issues)
        prerequisites = _tokens(
            table, row_number, "prerequisites", row["prerequisites"], issues
        )
        _known_tokens(table.name, row_number, "skills", skills, canonical_skills, issues)
        _known_tokens(
            table.name,
            row_number,
            "prerequisites",
            prerequisites,
            canonical_skills,
            issues,
        )
        _http_url(table.name, row_number, "source_url", row["source_url"], issues)
        _iso_date(table.name, row_number, "date_checked", row["date_checked"], issues)

def _validate_modules(
    table: _Table,
    resources: _Table,
    canonical_skills: set[str],
    issues: list[ValidationIssue],
) -> None:
    resource_by_id = {row["resource_id"].strip(): row for row in resources.rows}
    for row_number, row in enumerate(table.rows, start=2):
        parent_id = row["parent_resource_id"].strip()
        parent = resource_by_id.get(parent_id)
        if parent is None:
            issues.append(
                ValidationIssue(
                    table.name,
                    row_number,
                    "parent_resource_id",
                    f"unknown resource ID {parent_id!r}",
                )
            )
        elif row["provider"].strip() != parent["provider"].strip():
            issues.append(
                ValidationIssue(
                    table.name,
                    row_number,
                    "provider",
                    f"provider does not match parent resource {parent_id}",
                )
            )
        skills = _tokens(table, row_number, "skills", row["skills"], issues)
        _known_tokens(table.name, row_number, "skills", skills, canonical_skills, issues)
        _number_in_range(
            table.name,
            row_number,
            "difficulty_level",
            row["difficulty_level"],
            1,
            3,
            issues,
            integer=True,
        )
        duration = _number_in_range(
            table.name, row_number, "duration_hours", row["duration_hours"], 0, 1000, issues
        )
        if duration is not None and duration == 0:
            issues.append(
                ValidationIssue(
                    table.name, row_number, "duration_hours", "must be greater than 0"
                )
            )
        if parent is not None and duration is not None:
            parent_duration = _safe_float(parent["duration_hours"])
            if parent_duration is not None and duration > parent_duration:
                issues.append(
                    ValidationIssue(
                        table.name,
                        row_number,
                        "duration_hours",
                        f"exceeds parent resource duration {parent_duration:g}",
                    )
                )
        _http_url(table.name, row_number, "source_url", row["source_url"], issues)
        _iso_date(table.name, row_number, "date_checked", row["date_checked"], issues)
