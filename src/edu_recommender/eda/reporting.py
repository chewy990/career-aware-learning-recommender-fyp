"""Own eda reporting responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path


def _write_summary_markdown(
    findings: tuple[dict[str, str], ...],
    path: Path,
) -> None:
    sections = [
        "# Phase 2 Exploratory Data Analysis",
        "",
        ("All tables and figures in this summary are generated from the validated "
        "source CSVs. Pathway-relevance counts overlap because a resource can be "
        "relevant to more than one pathway."),
        "",
    ]
    for finding in findings:
        sections.extend(
            [
                f"## {finding['title']}",
                "",
                f"![{finding['title']}]({finding['figure']})",
                "",
                f"**Finding:** {finding['finding']}",
                "",
                f"**Implication:** {finding['implication']}",
                "",
            ]
        )
    path.write_text("\n".join(sections), encoding="utf-8")
