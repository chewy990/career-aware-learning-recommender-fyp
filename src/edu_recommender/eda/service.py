"""Own eda service responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

from edu_recommender.data import LearnerProfile, Resource, write_rows

from .contracts import FIGURE_FILES, TABLE_FIELDS, EdaResult
from .findings import _build_findings
from .reporting import _write_summary_markdown
from .tables import build_eda_tables


def generate_eda(
    resources: list[Resource],
    profiles: list[LearnerProfile],
    relevance: dict[str, set[str]],
    skill_map: dict[str, dict[str, int]],
    row_counts: dict[str, int],
    output_dir: Path,
) -> EdaResult:
    """Generate deterministic Phase 2 tables, figures, and interpretations."""
    tables = build_eda_tables(resources, profiles, relevance, skill_map, row_counts)
    findings = _build_findings(tables, resources)
    tables["eda_findings.csv"] = [dict(row) for row in findings]

    for filename, fieldnames in TABLE_FIELDS.items():
        write_rows(output_dir / filename, fieldnames, tables[filename])

    from .figures import _write_figures

    _write_figures(tables, output_dir)
    _write_summary_markdown(findings, output_dir / "eda_summary.md")

    output_files = (
        *TABLE_FIELDS,
        "eda_summary.md",
        *FIGURE_FILES,
    )
    return EdaResult(
        tables=tables,
        findings=findings,
        output_files=tuple(output_files),
    )
