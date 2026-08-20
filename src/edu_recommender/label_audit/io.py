"""Own label audit io responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import csv
from pathlib import Path


def _read_csv(path: Path, required_columns: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"Missing audit file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = tuple(reader.fieldnames or ())
        missing = [column for column in required_columns if column not in columns]
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

def _raise_id_mismatch(
    path: Path,
    actual: set[str],
    expected: set[str],
) -> None:
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    details = []
    if missing:
        details.append(f"missing IDs: {', '.join(missing)}")
    if unexpected:
        details.append(f"unexpected IDs: {', '.join(unexpected)}")
    raise ValueError(f"{path}: audit ID mismatch ({'; '.join(details)})")
