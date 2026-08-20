"""Own validation reference checks responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import re
from pathlib import Path

from .contracts import PATHWAYS, RESOURCE_FORMATS, SOURCE_TYPES, ValidationIssue, _Table
from .parsing import _http_url, _known_tokens, _skill_levels, _tokens
from .schemas import _allowed, _number_in_range


def _validate_profiles(
    table: _Table,
    canonical_skills: set[str],
    issues: list[ValidationIssue],
) -> None:
    for row_number, row in enumerate(table.rows, start=2):
        _allowed(
            table.name, row_number, "target_pathway", row["target_pathway"], set(PATHWAYS), issues
        )
        _allowed(
            table.name,
            row_number,
            "preferred_format",
            row["preferred_format"],
            RESOURCE_FORMATS,
            issues,
        )
        _number_in_range(
            table.name,
            row_number,
            "preferred_difficulty",
            row["preferred_difficulty"],
            1,
            3,
            issues,
            integer=True,
        )
        duration = _number_in_range(
            table.name,
            row_number,
            "max_duration_hours",
            row["max_duration_hours"],
            0,
            1000,
            issues,
        )
        if duration is not None and duration == 0:
            issues.append(
                ValidationIssue(
                    table.name, row_number, "max_duration_hours", "must be greater than 0"
                )
            )
        skill_levels = _skill_levels(table, row_number, row["current_skills"], issues)
        _known_tokens(
            table.name,
            row_number,
            "current_skills",
            set(skill_levels),
            canonical_skills,
            issues,
        )
        for skill, level in skill_levels.items():
            if not 0 <= level <= 3:
                issues.append(
                    ValidationIssue(
                        table.name,
                        row_number,
                        "current_skills",
                        f"level for {skill!r} must be between 0 and 3",
                    )
                )
        for column in ("completed_topics", "weak_skills"):
            tokens = _tokens(table, row_number, column, row[column], issues)
            _known_tokens(
                table.name, row_number, column, tokens, canonical_skills, issues
            )

def _validate_judgements(
    table: _Table,
    profiles: _Table,
    resources: _Table,
    issues: list[ValidationIssue],
) -> None:
    profile_ids = {row["profile_id"].strip() for row in profiles.rows}
    resource_ids = {row["resource_id"].strip() for row in resources.rows}
    judgement_ids = {row["profile_id"].strip() for row in table.rows}

    for missing_id in sorted(profile_ids - judgement_ids):
        issues.append(
            ValidationIssue(
                table.name,
                None,
                "profile_id",
                f"missing relevance judgement for profile {missing_id!r}",
            )
        )
    for extra_id in sorted(judgement_ids - profile_ids):
        issues.append(
            ValidationIssue(
                table.name,
                None,
                "profile_id",
                f"unknown profile ID {extra_id!r}",
            )
        )

    for row_number, row in enumerate(table.rows, start=2):
        relevant_ids = _tokens(
            table,
            row_number,
            "relevant_resource_ids",
            row["relevant_resource_ids"],
            issues,
        )
        unknown = sorted(relevant_ids - resource_ids)
        if unknown:
            issues.append(
                ValidationIssue(
                    table.name,
                    row_number,
                    "relevant_resource_ids",
                    f"unknown resource ID(s): {', '.join(unknown)}",
                )
            )
        positives = len(relevant_ids & resource_ids)
        negatives = len(resource_ids - relevant_ids)
        if positives == 0:
            issues.append(
                ValidationIssue(
                    table.name,
                    row_number,
                    "relevant_resource_ids",
                    "evaluation profile has no positive examples",
                )
            )
        if negatives == 0:
            issues.append(
                ValidationIssue(
                    table.name,
                    row_number,
                    "relevant_resource_ids",
                    "evaluation profile has no negative examples",
                )
            )


def _validate_graded_judgements(
    table: _Table,
    binary_judgements: _Table,
    issues: list[ValidationIssue],
) -> None:
    """Require one grade from 1 to 3 for every existing positive judgement."""

    expected_pairs = {
        (row["profile_id"].strip(), resource_id.strip())
        for row in binary_judgements.rows
        for resource_id in row["relevant_resource_ids"].split(";")
        if resource_id.strip()
    }
    actual_pairs: set[tuple[str, str]] = set()
    for row_number, row in enumerate(table.rows, start=2):
        pair = (row["profile_id"].strip(), row["resource_id"].strip())
        if pair in actual_pairs:
            issues.append(
                ValidationIssue(
                    table.name,
                    row_number,
                    None,
                    f"duplicate profile-resource pair {pair[0]}/{pair[1]}",
                )
            )
        actual_pairs.add(pair)
        _number_in_range(
            table.name,
            row_number,
            "relevance_grade",
            row["relevance_grade"],
            1,
            3,
            issues,
            integer=True,
        )
    for profile_id, resource_id in sorted(expected_pairs - actual_pairs):
        issues.append(
            ValidationIssue(
                table.name,
                None,
                None,
                f"missing grade for positive judgement {profile_id}/{resource_id}",
            )
        )
    for profile_id, resource_id in sorted(actual_pairs - expected_pairs):
        issues.append(
            ValidationIssue(
                table.name,
                None,
                None,
                f"grade does not match a positive judgement: {profile_id}/{resource_id}",
            )
        )

def _validate_sources(
    table: _Table,
    project_root: Path,
    issues: list[ValidationIssue],
) -> None:
    resolved_root = project_root.resolve()
    for row_number, row in enumerate(table.rows, start=2):
        _allowed(
            table.name, row_number, "source_type", row["source_type"], SOURCE_TYPES, issues
        )
        pathways = _tokens(
            table, row_number, "pathways_supported", row["pathways_supported"], issues
        )
        _known_tokens(
            table.name,
            row_number,
            "pathways_supported",
            pathways,
            set(PATHWAYS),
            issues,
        )
        skills = _tokens(
            table, row_number, "skills_supported", row["skills_supported"], issues
        )
        for skill in skills:
            if skill != "all" and not re.fullmatch(r"[a-z][a-z0-9_]*", skill):
                issues.append(
                    ValidationIssue(
                        table.name,
                        row_number,
                        "skills_supported",
                        f"invalid skill/category token {skill!r}",
                    )
                )
        reference = row["url"].strip()
        if reference.startswith(("http://", "https://")):
            _http_url(table.name, row_number, "url", reference, issues)
            continue
        candidate = (resolved_root / reference).resolve()
        try:
            candidate.relative_to(resolved_root)
        except ValueError:
            issues.append(
                ValidationIssue(
                    table.name,
                    row_number,
                    "url",
                    "local reference resolves outside the project folder",
                )
            )
            continue
        if not candidate.is_file():
            issues.append(
                ValidationIssue(
                    table.name,
                    row_number,
                    "url",
                    f"local reference does not exist: {reference}",
                )
            )
