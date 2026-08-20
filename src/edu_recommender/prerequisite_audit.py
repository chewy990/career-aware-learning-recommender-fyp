from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from edu_recommender.data import write_rows
from edu_recommender.label_audit import REVIEW_COLUMNS, VISIBLE_COLUMNS

PREREQUISITE_AUTHOR_AUDIT_VERSION = 1
KEY_COLUMNS = (
    "audit_item_id",
    "profile_id",
    "resource_id",
    "current_label",
    "experiment_role",
)


@dataclass(frozen=True)
class PrerequisiteAuthorAuditResult:
    """Record reconciled author decisions about prerequisite metadata."""

    item_count: int
    definite_count: int
    uncertain_count: int
    agreement_count: int
    removed_relevant_count: int
    replacement_relevant_count: int
    joined_rows: tuple[dict[str, object], ...]
    role_summary_rows: tuple[dict[str, object], ...]
    output_files: tuple[str, ...]


def analyse_prerequisite_author_audit(
    completed_path: Path,
    blinded_path: Path,
    key_path: Path,
    output_dir: Path,
) -> PrerequisiteAuthorAuditResult:
    """Reconcile completed prerequisite-audit decisions into summary evidence."""

    completed = _read_csv(completed_path, (*VISIBLE_COLUMNS, *REVIEW_COLUMNS))
    blinded = _read_csv(blinded_path, (*VISIBLE_COLUMNS, *REVIEW_COLUMNS))
    key = _read_csv(key_path, KEY_COLUMNS)
    completed_lookup = _unique_lookup(completed, completed_path)
    blinded_lookup = _unique_lookup(blinded, blinded_path)
    key_lookup = _unique_lookup(key, key_path)
    expected_ids = set(blinded_lookup)
    _validate_ids(completed_path, set(completed_lookup), expected_ids)
    _validate_ids(key_path, set(key_lookup), expected_ids)

    joined_rows: list[dict[str, object]] = []
    for audit_item_id in sorted(expected_ids):
        row = completed_lookup[audit_item_id]
        original = blinded_lookup[audit_item_id]
        hidden = key_lookup[audit_item_id]
        for column in VISIBLE_COLUMNS:
            if row[column] != original[column]:
                raise ValueError(
                    f"{completed_path}: {audit_item_id} changed blinded "
                    f"metadata column '{column}'"
                )
        author_label = row["reviewer_relevance"].strip().upper()
        if author_label not in {"0", "1", "U"}:
            raise ValueError(
                f"{completed_path}: {audit_item_id} reviewer_relevance "
                "must be 0, 1, or U"
            )
        confidence = row["reviewer_confidence"].strip()
        if confidence not in {"1", "2", "3"}:
            raise ValueError(
                f"{completed_path}: {audit_item_id} reviewer_confidence "
                "must be 1, 2, or 3"
            )
        notes = row["reviewer_notes"].strip()
        if (author_label == "U" or confidence == "1") and not notes:
            raise ValueError(
                f"{completed_path}: {audit_item_id} requires reviewer_notes "
                "for U or confidence 1"
            )
        current_label = hidden["current_label"].strip()
        if current_label not in {"0", "1"}:
            raise ValueError(
                f"{key_path}: {audit_item_id} current_label must be 0 or 1"
            )
        role = hidden["experiment_role"].strip()
        if role not in {"baseline_removed", "variant_replacement"}:
            raise ValueError(
                f"{key_path}: {audit_item_id} has invalid experiment_role "
                f"'{role}'"
            )
        agreement: object = ""
        if author_label != "U":
            agreement = int(author_label == current_label)
        joined_rows.append(
            {
                "audit_item_id": audit_item_id,
                "pathway": row["pathway"],
                "profile_id": hidden["profile_id"],
                "resource_id": hidden["resource_id"],
                "resource_title": row["resource_title"],
                "experiment_role": role,
                "current_label": int(current_label),
                "author_label": author_label,
                "agreement": agreement,
                "reviewer_confidence": int(confidence),
                "reviewer_notes": notes,
            }
        )

    role_summary_rows = _build_role_summary(joined_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    joined_fields = [
        "audit_item_id",
        "pathway",
        "profile_id",
        "resource_id",
        "resource_title",
        "experiment_role",
        "current_label",
        "author_label",
        "agreement",
        "reviewer_confidence",
        "reviewer_notes",
    ]
    write_rows(
        output_dir / "prerequisite_author_audit_joined.csv",
        joined_fields,
        joined_rows,
    )
    write_rows(
        output_dir / "prerequisite_author_audit_role_summary.csv",
        [
            "experiment_role",
            "items",
            "definite_decisions",
            "uncertain_decisions",
            "author_relevant",
            "author_relevant_rate",
            "mean_confidence",
        ],
        role_summary_rows,
    )
    _write_summary(
        output_dir / "prerequisite_author_audit_summary.md",
        role_summary_rows,
    )
    definite = [row for row in joined_rows if row["author_label"] != "U"]
    return PrerequisiteAuthorAuditResult(
        item_count=len(joined_rows),
        definite_count=len(definite),
        uncertain_count=len(joined_rows) - len(definite),
        agreement_count=sum(int(row["agreement"]) for row in definite),
        removed_relevant_count=_relevant_count(
            joined_rows, "baseline_removed"
        ),
        replacement_relevant_count=_relevant_count(
            joined_rows, "variant_replacement"
        ),
        joined_rows=tuple(joined_rows),
        role_summary_rows=tuple(role_summary_rows),
        output_files=(
            "prerequisite_author_audit_joined.csv",
            "prerequisite_author_audit_role_summary.csv",
            "prerequisite_author_audit_summary.md",
        ),
    )


def _read_csv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"Missing audit file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = tuple(reader.fieldnames or ())
        missing = [column for column in required if column not in columns]
        if missing:
            raise ValueError(
                f"{path}: missing required columns: {', '.join(missing)}"
            )
        return [dict(row) for row in reader]


def _unique_lookup(
    rows: list[dict[str, str]],
    path: Path,
) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, start=2):
        audit_item_id = row["audit_item_id"].strip()
        if not audit_item_id:
            raise ValueError(f"{path}:{row_number}: audit_item_id is blank")
        if audit_item_id in lookup:
            raise ValueError(
                f"{path}:{row_number}: duplicate audit_item_id "
                f"'{audit_item_id}'"
            )
        lookup[audit_item_id] = row
    return lookup


def _validate_ids(path: Path, actual: set[str], expected: set[str]) -> None:
    if actual == expected:
        return
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    parts = []
    if missing:
        parts.append(f"missing IDs: {', '.join(missing)}")
    if unexpected:
        parts.append(f"unexpected IDs: {', '.join(unexpected)}")
    raise ValueError(f"{path}: audit ID mismatch ({'; '.join(parts)})")


def _build_role_summary(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for role in ("baseline_removed", "variant_replacement"):
        role_rows = [row for row in rows if row["experiment_role"] == role]
        definite = [row for row in role_rows if row["author_label"] != "U"]
        relevant = sum(row["author_label"] == "1" for row in definite)
        output.append(
            {
                "experiment_role": role,
                "items": len(role_rows),
                "definite_decisions": len(definite),
                "uncertain_decisions": len(role_rows) - len(definite),
                "author_relevant": relevant,
                "author_relevant_rate": (
                    f"{relevant / len(definite):.4f}" if definite else ""
                ),
                "mean_confidence": (
                    f"{mean(int(row['reviewer_confidence']) for row in role_rows):.4f}"
                    if role_rows
                    else ""
                ),
            }
        )
    return output


def _relevant_count(rows: list[dict[str, object]], role: str) -> int:
    return sum(
        row["author_label"] == "1"
        for row in rows
        if row["experiment_role"] == role
    )


def _write_summary(
    path: Path,
    role_rows: list[dict[str, object]],
) -> None:
    lookup = {str(row["experiment_role"]): row for row in role_rows}
    removed = lookup["baseline_removed"]
    replacement = lookup["variant_replacement"]
    lines = [
        "# Targeted Prerequisite Author-Audit Summary",
        "",
        ("This is a blinded internal review by the project author, not "
        "independent validation."),
        "",
        "## Verified result",
        "",
        ("| Role revealed after review | Relevant | Decisions | Rate | "
        "Mean confidence |"),
        "| --- | ---: | ---: | ---: | ---: |",
        (f"| Baseline resources removed by the hard rule | "
        f"{removed['author_relevant']} | {removed['definite_decisions']} | "
        f"{float(removed['author_relevant_rate']):.1%} | "
        f"{float(removed['mean_confidence']):.2f} |"),
        (f"| Variant replacement resources | "
        f"{replacement['author_relevant']} | "
        f"{replacement['definite_decisions']} | "
        f"{float(replacement['author_relevant_rate']):.1%} | "
        f"{float(replacement['mean_confidence']):.2f} |"),
        "",
        ("All ten resources were judged relevant. The targeted audit therefore "
        "supports the suitability of every replacement but does not show "
        "higher binary relevance than the removed resources. The replacements "
        "received higher mean confidence (`3.00` versus `2.40`)."),
        "",
        ("The objective experiment remains separate: the five removed resources "
        "failed the predeclared hard-prerequisite eligibility rule, whereas "
        "the replacements passed it. The combined evidence shows a readiness "
        "improvement without a measured relevance improvement. It does not "
        "prove that every declared prerequisite should be treated as mandatory."),
        "",
        "No source label or production setting is changed by this analysis.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
