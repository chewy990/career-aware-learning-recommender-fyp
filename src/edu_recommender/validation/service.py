"""Own validation service responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

from .contracts import (
    _SPECS,
    GRADED_JUDGEMENT_COLUMNS,
    JUDGEMENT_COLUMNS,
    MODULE_COLUMNS,
    PROFILE_COLUMNS,
    RESOURCE_COLUMNS,
    SKILL_MAP_COLUMNS,
    SOURCE_COLUMNS,
    DataValidationError,
    ValidationIssue,
    ValidationSummary,
    _Table,
)
from .dataset_validators import (
    _validate_modules,
    _validate_resources,
    _validate_skill_map,
)
from .parsing import _read_table
from .reference_checks import (
    _validate_graded_judgements,
    _validate_judgements,
    _validate_profiles,
    _validate_sources,
)
from .schemas import (
    _has_columns,
    _validate_ids,
    _validate_required_values,
    _validate_schema,
)


def validate_data_dir(data_dir: Path) -> ValidationSummary:
    """Validate all Phase 1 CSV inputs and return a report-ready summary."""
    data_dir = Path(data_dir)
    issues: list[ValidationIssue] = []
    tables: dict[str, _Table] = {}

    for name, (required_columns, id_column, id_pattern) in _SPECS.items():
        table = _read_table(data_dir / name, issues)
        if table is None:
            continue
        tables[name] = table
        _validate_schema(table, required_columns, issues)
        if _has_columns(table, required_columns):
            _validate_required_values(table, required_columns, issues)
            _validate_ids(table, id_column, id_pattern, issues)

    skill_table = tables.get("skill_map.csv")
    canonical_skills = (
        {row["skill"].strip() for row in skill_table.rows if row.get("skill", "").strip()}
        if skill_table and _has_columns(skill_table, SKILL_MAP_COLUMNS)
        else set()
    )

    if skill_table and _has_columns(skill_table, SKILL_MAP_COLUMNS):
        _validate_skill_map(skill_table, issues)

    resource_table = tables.get("resources.csv")
    if resource_table and _has_columns(resource_table, RESOURCE_COLUMNS):
        _validate_resources(resource_table, canonical_skills, issues)

    module_table = tables.get("resource_modules.csv")
    if (
        module_table
        and resource_table
        and _has_columns(module_table, MODULE_COLUMNS)
        and _has_columns(resource_table, RESOURCE_COLUMNS)
    ):
        _validate_modules(module_table, resource_table, canonical_skills, issues)

    profile_table = tables.get("learner_profiles.csv")
    if profile_table and _has_columns(profile_table, PROFILE_COLUMNS):
        _validate_profiles(profile_table, canonical_skills, issues)

    judgement_table = tables.get("relevance_judgements.csv")
    if (
        judgement_table
        and profile_table
        and resource_table
        and _has_columns(judgement_table, JUDGEMENT_COLUMNS)
        and _has_columns(profile_table, PROFILE_COLUMNS)
        and _has_columns(resource_table, RESOURCE_COLUMNS)
    ):
        _validate_judgements(judgement_table, profile_table, resource_table, issues)

    graded_path = data_dir / "relevance_judgements_graded.csv"
    if graded_path.is_file():
        graded_table = _read_table(graded_path, issues)
        if graded_table is not None:
            tables[graded_path.name] = graded_table
            _validate_schema(graded_table, GRADED_JUDGEMENT_COLUMNS, issues)
            if _has_columns(graded_table, GRADED_JUDGEMENT_COLUMNS):
                _validate_required_values(
                    graded_table,
                    GRADED_JUDGEMENT_COLUMNS,
                    issues,
                )
                if judgement_table:
                    _validate_graded_judgements(
                        graded_table,
                        judgement_table,
                        issues,
                    )

    source_table = tables.get("skill_sources.csv")
    if source_table and _has_columns(source_table, SOURCE_COLUMNS):
        _validate_sources(source_table, data_dir.parent, issues)

    if issues:
        raise DataValidationError(issues)

    row_counts = {name: len(table.rows) for name, table in sorted(tables.items())}
    checks: list[dict[str, str]] = []
    for name, table in sorted(tables.items()):
        checks.append(
            {
                "dataset": name,
                "check": "schema_ids_values_references",
                "status": "passed",
                "details": f"{len(table.rows)} rows validated",
            }
        )
    checks.append(
        {
            "dataset": "evaluation",
            "check": "profile_label_coverage",
            "status": "passed",
            "details": (
                f"{len(profile_table.rows) if profile_table else 0} profiles have "
                "positive and negative examples"
            ),
        }
    )
    return ValidationSummary(row_counts=row_counts, checks=tuple(checks))
