"""Own validation schemas responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import re

from .contracts import PATHWAYS, ValidationIssue, _Table


def _validate_schema(
    table: _Table,
    required_columns: tuple[str, ...],
    issues: list[ValidationIssue],
) -> None:
    duplicates = sorted({header for header in table.headers if table.headers.count(header) > 1})
    if duplicates:
        issues.append(
            ValidationIssue(
                table.name,
                1,
                None,
                f"duplicate column name(s): {', '.join(duplicates)}",
            )
        )
    missing = [column for column in required_columns if column not in table.headers]
    if missing:
        issues.append(
            ValidationIssue(
                table.name,
                1,
                None,
                f"missing required column(s): {', '.join(missing)}",
            )
        )
    if table.name == "resources.csv":
        actual = {header for header in table.headers if header.endswith("_relevance")}
        expected = {f"{pathway}_relevance" for pathway in PATHWAYS}
        unknown = sorted(actual - expected)
        if unknown:
            issues.append(
                ValidationIssue(
                    table.name,
                    1,
                    None,
                    f"unknown pathway relevance column(s): {', '.join(unknown)}",
                )
            )
    if table.name == "skill_map.csv":
        unknown = sorted(set(table.headers) - {"skill", *PATHWAYS})
        if unknown:
            issues.append(
                ValidationIssue(
                    table.name,
                    1,
                    None,
                    f"unknown pathway column(s): {', '.join(unknown)}",
                )
            )

def _validate_required_values(
    table: _Table,
    required_columns: tuple[str, ...],
    issues: list[ValidationIssue],
) -> None:
    optional_blank = {
        ("resources.csv", "prerequisites"),
        ("learner_profiles.csv", "completed_topics"),
        ("learner_profiles.csv", "weak_skills"),
    }
    if not table.rows:
        issues.append(ValidationIssue(table.name, None, None, "dataset has no data rows"))
    for row_number, row in enumerate(table.rows, start=2):
        for column in required_columns:
            if (table.name, column) in optional_blank:
                continue
            if not row.get(column, "").strip():
                issues.append(
                    ValidationIssue(table.name, row_number, column, "required value is blank")
                )

def _validate_ids(
    table: _Table,
    id_column: str,
    pattern: re.Pattern[str],
    issues: list[ValidationIssue],
) -> None:
    seen: dict[str, int] = {}
    for row_number, row in enumerate(table.rows, start=2):
        value = row.get(id_column, "").strip()
        if not value:
            continue
        if not pattern.fullmatch(value):
            issues.append(
                ValidationIssue(
                    table.name,
                    row_number,
                    id_column,
                    f"invalid ID {value!r}; expected pattern {pattern.pattern}",
                )
            )
        if value in seen:
            issues.append(
                ValidationIssue(
                    table.name,
                    row_number,
                    id_column,
                    f"duplicate ID {value!r}; first seen on row {seen[value]}",
                )
            )
        else:
            seen[value] = row_number

def _has_columns(table: _Table, columns: tuple[str, ...]) -> bool:
    return all(column in table.headers for column in columns)

def _allowed(
    dataset: str,
    row: int,
    column: str,
    value: str,
    allowed: set[str],
    issues: list[ValidationIssue],
) -> None:
    if value.strip() not in allowed:
        issues.append(
            ValidationIssue(
                dataset,
                row,
                column,
                f"invalid category {value.strip()!r}; allowed: {', '.join(sorted(allowed))}",
            )
        )

def _number_in_range(
    dataset: str,
    row: int,
    column: str,
    value: str,
    minimum: float,
    maximum: float,
    issues: list[ValidationIssue],
    *,
    integer: bool = False,
) -> float | None:
    try:
        number = float(value)
    except ValueError:
        issues.append(
            ValidationIssue(dataset, row, column, f"expected a numeric value, got {value!r}")
        )
        return None
    if integer and not number.is_integer():
        issues.append(
            ValidationIssue(dataset, row, column, f"expected an integer, got {value!r}")
        )
        return None
    if not minimum <= number <= maximum:
        issues.append(
            ValidationIssue(
                dataset,
                row,
                column,
                f"value {value!r} is outside the allowed range {minimum:g} to {maximum:g}",
            )
        )
    return number
