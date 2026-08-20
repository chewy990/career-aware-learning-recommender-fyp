from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

from generate_graded_relevance_pack import VISIBLE_COLUMNS, generate_pack

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = ROOT / "outputs" / "graded_relevance_working"
DEFAULT_OUTPUT = ROOT / "data" / "relevance_judgements_graded.csv"


def apply_completed_grades(
    completed_path: Path,
    output_path: Path,
    pack_dir: Path = DEFAULT_PACK,
) -> int:
    """Validate a completed blinded export and write canonical long-form grades."""

    blinded_path, key_path = generate_pack(pack_dir)
    blinded = _read_lookup(blinded_path, VISIBLE_COLUMNS)
    completed = _read_completed(completed_path, blinded_path, blinded)
    key = _read_lookup(
        key_path,
        ("grading_item_id", "profile_id", "resource_id"),
    )
    if set(completed) != set(blinded):
        raise ValueError("completed sheet has missing or unexpected grading item IDs")

    canonical_rows: list[dict[str, object]] = []
    for item_id in sorted(blinded):
        row = completed[item_id]
        original = blinded[item_id]
        for column in VISIBLE_COLUMNS[:-3]:
            if row[column] != original[column]:
                raise ValueError(f"{item_id}: metadata column {column!r} was changed")
        grade = row["relevance_grade"].strip()
        confidence = row["reviewer_confidence"].strip()
        notes = row["reviewer_notes"].strip()
        if grade not in {"1", "2", "3"}:
            raise ValueError(f"{item_id}: relevance_grade must be 1, 2, or 3")
        if confidence not in {"1", "2", "3"}:
            raise ValueError(f"{item_id}: reviewer_confidence must be 1, 2, or 3")
        if confidence == "1" and not notes:
            raise ValueError(f"{item_id}: reviewer_notes is required for confidence 1")
        canonical_rows.append(
            {
                "profile_id": key[item_id]["profile_id"],
                "resource_id": key[item_id]["resource_id"],
                "relevance_grade": int(grade),
            }
        )

    canonical_rows.sort(key=lambda row: (str(row["profile_id"]), str(row["resource_id"])))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=("profile_id", "resource_id", "relevance_grade"),
        )
        writer.writeheader()
        writer.writerows(canonical_rows)
    archived = pack_dir / "graded_relevance_completed.csv"
    _write_completed_csv(archived, completed)
    if completed_path.suffix.casefold() == ".json":
        archived_backup = pack_dir / "graded_relevance_progress.json"
        if completed_path.resolve() != archived_backup.resolve():
            shutil.copyfile(completed_path, archived_backup)
    return len(canonical_rows)


def _read_completed(
    path: Path,
    blinded_path: Path,
    blinded: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    if path.suffix.casefold() != ".json":
        return _read_lookup(path, VISIBLE_COLUMNS)
    if not path.is_file():
        raise ValueError(f"missing progress backup: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        answers = payload["state"]["answers"]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: invalid progress backup structure") from error
    expected_pack = (
        "graded-relevance-review-"
        + hashlib.sha256(blinded_path.read_bytes()).hexdigest()[:16]
    )
    if payload.get("pack") != expected_pack:
        raise ValueError(f"{path}: backup does not match the current grading pack")
    if not isinstance(answers, dict) or set(answers) != set(blinded):
        raise ValueError(f"{path}: backup has missing or unexpected grading item IDs")
    completed: dict[str, dict[str, str]] = {}
    for item_id, original in blinded.items():
        answer = answers.get(item_id)
        if not isinstance(answer, dict):
            raise TypeError(f"{path}: invalid answer for {item_id}")
        completed[item_id] = {
            **original,
            "relevance_grade": str(answer.get("grade", "")),
            "reviewer_confidence": str(answer.get("confidence", "")),
            "reviewer_notes": str(answer.get("notes", "")),
        }
    return completed


def _write_completed_csv(
    path: Path,
    completed: dict[str, dict[str, str]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=VISIBLE_COLUMNS)
        writer.writeheader()
        writer.writerows(completed[item_id] for item_id in sorted(completed))


def _read_lookup(path: Path, required: tuple[str, ...]) -> dict[str, dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = [column for column in required if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(missing)}")
        rows: dict[str, dict[str, str]] = {}
        for row_number, row in enumerate(reader, start=2):
            item_id = row["grading_item_id"].strip()
            if not item_id:
                raise ValueError(f"{path}:{row_number}: blank grading_item_id")
            if item_id in rows:
                raise ValueError(f"{path}:{row_number}: duplicate grading_item_id {item_id}")
            rows[item_id] = dict(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and apply completed relevance grades.")
    parser.add_argument(
        "completed_review",
        type=Path,
        help="Completed CSV export or browser progress JSON backup.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        count = apply_completed_grades(
            args.completed_review.resolve(),
            args.output.resolve(),
        )
    except (TypeError, ValueError) as error:
        print(f"Graded relevance validation failed: {error}", file=sys.stderr)
        return 1
    print(f"Applied {count} graded relevance judgements to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
