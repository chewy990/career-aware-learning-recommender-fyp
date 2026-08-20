"""Own validation parsing responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from .contracts import ValidationIssue, _Table


def _read_table(path: Path, issues: list[ValidationIssue]) -> _Table | None:
    if not path.is_file():
        issues.append(ValidationIssue(path.name, None, None, "required CSV file is missing"))
        return None
    try:
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            headers = list(reader.fieldnames or [])
            rows = [
                {key: (value if value is not None else "") for key, value in row.items()}
                for row in reader
            ]
    except (OSError, UnicodeError, csv.Error) as error:
        issues.append(ValidationIssue(path.name, None, None, f"could not read CSV: {error}"))
        return None
    if not headers:
        issues.append(ValidationIssue(path.name, None, None, "CSV header is missing"))
    return _Table(path.name, path, headers, rows)

def _tokens(
    table: _Table,
    row: int,
    column: str,
    value: str,
    issues: list[ValidationIssue],
) -> set[str]:
    raw_tokens = [token.strip() for token in value.split(";") if token.strip()]
    duplicates = sorted({token for token in raw_tokens if raw_tokens.count(token) > 1})
    if duplicates:
        issues.append(
            ValidationIssue(
                table.name,
                row,
                column,
                f"duplicate token(s): {', '.join(duplicates)}",
            )
        )
    return set(raw_tokens)

def _skill_levels(
    table: _Table,
    row: int,
    value: str,
    issues: list[ValidationIssue],
) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in (item.strip() for item in value.split(";") if item.strip()):
        if ":" not in item:
            issues.append(
                ValidationIssue(
                    table.name,
                    row,
                    "current_skills",
                    f"invalid skill level {item!r}; expected skill:level",
                )
            )
            continue
        skill, raw_level = (part.strip() for part in item.split(":", maxsplit=1))
        if skill in result:
            issues.append(
                ValidationIssue(
                    table.name,
                    row,
                    "current_skills",
                    f"duplicate skill {skill!r}",
                )
            )
            continue
        try:
            result[skill] = int(raw_level)
        except ValueError:
            issues.append(
                ValidationIssue(
                    table.name,
                    row,
                    "current_skills",
                    f"invalid integer level {raw_level!r} for {skill!r}",
                )
            )
    return result

def _known_tokens(
    dataset: str,
    row: int,
    column: str,
    tokens: set[str],
    known: set[str],
    issues: list[ValidationIssue],
) -> None:
    unknown = sorted(tokens - known)
    if unknown:
        issues.append(
            ValidationIssue(
                dataset,
                row,
                column,
                f"unknown value(s): {', '.join(unknown)}",
            )
        )

def _http_url(
    dataset: str,
    row: int,
    column: str,
    value: str,
    issues: list[ValidationIssue],
) -> None:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        issues.append(
            ValidationIssue(dataset, row, column, f"invalid HTTP(S) URL {value!r}")
        )

def _iso_date(
    dataset: str,
    row: int,
    column: str,
    value: str,
    issues: list[ValidationIssue],
) -> None:
    try:
        date.fromisoformat(value.strip())
    except ValueError:
        issues.append(
            ValidationIssue(dataset, row, column, f"invalid ISO date {value!r}")
        )

def _safe_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None

def _safe_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None
