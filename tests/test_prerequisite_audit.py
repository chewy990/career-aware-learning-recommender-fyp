from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from edu_recommender.label_audit import (
    REVIEW_COLUMNS,
    VISIBLE_COLUMNS,
)
from edu_recommender.prerequisite_audit import (
    KEY_COLUMNS,
    analyse_prerequisite_author_audit,
)


class PrerequisiteAuthorAuditTests(unittest.TestCase):
    def test_roles_are_revealed_and_compared_after_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blinded, completed, key = self._write_fixture(root)
            result = analyse_prerequisite_author_audit(
                completed,
                blinded,
                key,
                root / "output",
            )

            self.assertEqual(result.item_count, 2)
            self.assertEqual(result.agreement_count, 1)
            self.assertEqual(result.removed_relevant_count, 0)
            self.assertEqual(result.replacement_relevant_count, 1)
            self.assertTrue(
                (
                    root
                    / "output/prerequisite_author_audit_summary.md"
                ).is_file()
            )

    def test_changed_blinded_metadata_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blinded, completed, key = self._write_fixture(root)
            rows = self._read(completed)
            rows[0]["pathway"] = "changed"
            self._write(completed, (*VISIBLE_COLUMNS, *REVIEW_COLUMNS), rows)

            with self.assertRaisesRegex(ValueError, "changed blinded metadata"):
                analyse_prerequisite_author_audit(
                    completed,
                    blinded,
                    key,
                    root / "output",
                )

    @classmethod
    def _write_fixture(cls, root: Path) -> tuple[Path, Path, Path]:
        blinded = root / "blinded.csv"
        completed = root / "completed.csv"
        key = root / "key.csv"
        visible = [
            cls._visible_row("H001", "Removed"),
            cls._visible_row("H002", "Replacement"),
        ]
        cls._write(
            blinded,
            (*VISIBLE_COLUMNS, *REVIEW_COLUMNS),
            [
                {
                    **row,
                    "reviewer_relevance": "",
                    "reviewer_confidence": "",
                    "reviewer_notes": "",
                }
                for row in visible
            ],
        )
        cls._write(
            completed,
            (*VISIBLE_COLUMNS, *REVIEW_COLUMNS),
            [
                {
                    **visible[0],
                    "reviewer_relevance": "0",
                    "reviewer_confidence": "3",
                    "reviewer_notes": "",
                },
                {
                    **visible[1],
                    "reviewer_relevance": "1",
                    "reviewer_confidence": "3",
                    "reviewer_notes": "",
                },
            ],
        )
        cls._write(
            key,
            KEY_COLUMNS,
            [
                {
                    "audit_item_id": "H001",
                    "profile_id": "P001",
                    "resource_id": "R001",
                    "current_label": "1",
                    "experiment_role": "baseline_removed",
                },
                {
                    "audit_item_id": "H002",
                    "profile_id": "P001",
                    "resource_id": "R002",
                    "current_label": "1",
                    "experiment_role": "variant_replacement",
                },
            ],
        )
        return blinded, completed, key

    @staticmethod
    def _visible_row(item_id: str, title: str) -> dict[str, str]:
        return {
            "audit_item_id": item_id,
            "pathway": "data_scientist",
            "profile_name": "Test learner",
            "target_pathway": "data_scientist",
            "current_skills": "python:1",
            "weak_skills": "statistics",
            "preferred_difficulty": "1",
            "resource_title": title,
            "provider": "Provider",
            "topic": "statistics",
            "skills": "statistics",
            "resource_difficulty": "2",
            "format": "course",
            "prerequisites": "python",
        }

    @staticmethod
    def _read(path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    @staticmethod
    def _write(
        path: Path,
        fieldnames: tuple[str, ...],
        rows: list[dict[str, str]],
    ) -> None:
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
