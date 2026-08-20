"""Own label audit reporting responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path


def _build_summary_rows(
    joined_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    groups: list[tuple[str, str, list[dict[str, object]]]] = [
        ("overall", "all", joined_rows)
    ]
    for dimension, key in (
        ("pathway", "pathway"),
        ("selection_reason", "selection_reason"),
        ("confidence", "reviewer_confidence"),
    ):
        categories = sorted({str(row[key]) for row in joined_rows})
        groups.extend(
            (
                dimension,
                category,
                [row for row in joined_rows if str(row[key]) == category],
            )
            for category in categories
        )

    summary_rows: list[dict[str, object]] = []
    for dimension, category, rows in groups:
        definite = [row for row in rows if row["author_label"] != "U"]
        agreements = sum(int(row["agreement"]) for row in definite)
        summary_rows.append(
            {
                "dimension": dimension,
                "category": category,
                "total_items": len(rows),
                "definite_decisions": len(definite),
                "uncertain_decisions": len(rows) - len(definite),
                "agreements": agreements,
                "disagreements": len(definite) - agreements,
                "agreement_rate": (
                    f"{agreements / len(definite):.4f}"
                    if definite
                    else ""
                ),
            }
        )
    return summary_rows

def _write_summary_markdown(
    path: Path,
    joined_rows: list[dict[str, object]],
    summary_rows: list[dict[str, object]],
) -> None:
    overall = summary_rows[0]
    disagreement_rows = [
        row
        for row in joined_rows
        if row["author_label"] != "U" and not bool(row["agreement"])
    ]
    current_positive = sum(
        int(row["current_label"]) for row in joined_rows
    )
    author_positive = sum(
        row["author_label"] == "1" for row in joined_rows
    )
    lines = [
        "# Blinded Author Relevance-Label Audit Summary",
        "",
        ("This is an internal consistency audit by the project author. "
        "It is not independent validation or an inter-rater reliability study."),
        "",
        "## Verified result",
        "",
        f"- Items: `{overall['total_items']}`",
        f"- Definite decisions: `{overall['definite_decisions']}`",
        f"- Uncertain decisions: `{overall['uncertain_decisions']}`",
        f"- Agreements: `{overall['agreements']}`",
        f"- Disagreements: `{overall['disagreements']}`",
        (f"- Raw author-to-current-label agreement: "
        f"`{float(overall['agreement_rate']):.1%}`"),
        (f"- Current positive labels in the stratified sample: "
        f"`{current_positive}`"),
        f"- Author positive decisions in the sample: `{author_positive}`",
        "",
        ("The sample was deliberately balanced across pathways and case types, "
        "so its label proportions are not estimates of full-dataset prevalence."),
        "",
        "## Agreement by pathway",
        "",
        "| Pathway | Decisions | Agreements | Rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        if row["dimension"] != "pathway":
            continue
        lines.append(
            f"| {row['category']} | {row['definite_decisions']} | "
            f"{row['agreements']} | "
            f"{float(row['agreement_rate']):.1%} |"
        )
    lines.extend(
        [
            "",
            "## Disagreements requiring an explicit decision",
            "",
            "| ID | Pathway | Resource | Current | Author | Confidence |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in disagreement_rows:
        lines.append(
            f"| {row['audit_item_id']} | {row['pathway']} | "
            f"{row['resource_title']} | {row['current_label']} | "
            f"{row['author_label']} | {row['reviewer_confidence']} |"
        )
    lines.extend(
        [
            "",
            ("No source label is changed by this analysis. Each disagreement "
            "must be retained or accepted with a documented reason before a "
            "versioned label revision is created."),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
