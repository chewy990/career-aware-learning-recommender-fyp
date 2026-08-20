"""Own robustness reporting responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path


def _write_summary(
    findings: tuple[dict[str, str], ...],
    figures: tuple[str, ...],
    output_dir: Path,
) -> None:
    figure_lookup = {
        findings[0]["title"]: figures[0],
        findings[1]["title"]: figures[0],
        findings[2]["title"]: figures[1],
        findings[3]["title"]: figures[2],
        findings[4]["title"]: figures[3],
        findings[5]["title"]: figures[3],
    }
    sections = []
    for finding in findings:
        sections.append(
            f"## {finding['title']}\n\n"
            f"![{finding['title']}]({figure_lookup[finding['title']]})\n\n"
            f"**Finding:** {finding['finding']}\n\n"
            f"**Implication:** {finding['implication']}\n"
        )
    text = (
        "# Phase 4 Hybrid Robustness And Explainability\n\n"
        "This analysis uses the unchanged Phase 3 data and baseline hybrid. "
        "Ablations and weight variants are diagnostic experiments only; no "
        "variant is selected or written back into the production model.\n\n"
        + "\n".join(sections)
    )
    (output_dir / "phase4_summary.md").write_text(
        text,
        encoding="utf-8",
    )

def _humanise(value: str) -> str:
    acronyms = {
        "ndcg": "NDCG",
        "api": "API",
        "apis": "APIs",
    }
    return " ".join(
        acronyms.get(part, part.capitalize())
        for part in value.split("_")
    )
