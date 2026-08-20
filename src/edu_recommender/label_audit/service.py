"""Own label audit service responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

from edu_recommender.data import write_rows

from .contracts import KEY_COLUMNS, REVIEW_COLUMNS, VISIBLE_COLUMNS, AuthorAuditResult
from .io import _raise_id_mismatch, _read_csv, _unique_lookup
from .reporting import _build_summary_rows, _write_summary_markdown


def analyse_author_audit(
    completed_path: Path,
    blinded_path: Path,
    key_path: Path,
    output_dir: Path,
) -> AuthorAuditResult:
    """Reconcile completed relevance-audit decisions into deterministic summary evidence."""

    completed = _read_csv(completed_path, (*VISIBLE_COLUMNS, *REVIEW_COLUMNS))
    blinded = _read_csv(blinded_path, (*VISIBLE_COLUMNS, *REVIEW_COLUMNS))
    key = _read_csv(key_path, KEY_COLUMNS)

    completed_lookup = _unique_lookup(completed, completed_path)
    blinded_lookup = _unique_lookup(blinded, blinded_path)
    key_lookup = _unique_lookup(key, key_path)
    expected_ids = set(blinded_lookup)
    if set(completed_lookup) != expected_ids:
        _raise_id_mismatch(completed_path, set(completed_lookup), expected_ids)
    if set(key_lookup) != expected_ids:
        _raise_id_mismatch(key_path, set(key_lookup), expected_ids)

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
                "current_label": int(current_label),
                "author_label": author_label,
                "agreement": agreement,
                "reviewer_confidence": int(confidence),
                "selection_reason": hidden["selection_reason"],
                "reviewer_notes": notes,
            }
        )

    definite_rows = [row for row in joined_rows if row["author_label"] != "U"]
    uncertain_count = len(joined_rows) - len(definite_rows)
    agreement_count = sum(int(row["agreement"]) for row in definite_rows)
    disagreement_rows = [
        row for row in definite_rows if not bool(row["agreement"])
    ]
    agreement_rate = (
        agreement_count / len(definite_rows) if definite_rows else 0.0
    )
    summary_rows = _build_summary_rows(joined_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    joined_fields = [
        "audit_item_id",
        "pathway",
        "profile_id",
        "resource_id",
        "resource_title",
        "current_label",
        "author_label",
        "agreement",
        "reviewer_confidence",
        "selection_reason",
        "reviewer_notes",
    ]
    write_rows(
        output_dir / "author_audit_joined.csv",
        joined_fields,
        joined_rows,
    )
    write_rows(
        output_dir / "author_audit_disagreements.csv",
        joined_fields,
        disagreement_rows,
    )
    write_rows(
        output_dir / "author_audit_summary.csv",
        [
            "dimension",
            "category",
            "total_items",
            "definite_decisions",
            "uncertain_decisions",
            "agreements",
            "disagreements",
            "agreement_rate",
        ],
        summary_rows,
    )
    _write_summary_markdown(
        output_dir / "author_audit_summary.md",
        joined_rows,
        summary_rows,
    )
    return AuthorAuditResult(
        item_count=len(joined_rows),
        definite_count=len(definite_rows),
        uncertain_count=uncertain_count,
        agreement_count=agreement_count,
        disagreement_count=len(disagreement_rows),
        agreement_rate=agreement_rate,
        joined_rows=tuple(joined_rows),
        disagreement_rows=tuple(disagreement_rows),
        summary_rows=tuple(summary_rows),
        output_files=(
            "author_audit_joined.csv",
            "author_audit_disagreements.csv",
            "author_audit_summary.csv",
            "author_audit_summary.md",
        ),
    )
