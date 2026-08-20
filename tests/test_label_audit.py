from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from edu_recommender.label_audit import (
    KEY_COLUMNS,
    REVIEW_COLUMNS,
    VISIBLE_COLUMNS,
    analyse_author_audit,
)
from run_author_audit import run_author_audit


class AuthorAuditTests(unittest.TestCase):
    def test_author_audit_runner_hashes_the_current_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            run_author_audit(
                ROOT / "outputs/author_audit_run/input/relevance_audit_completed.csv",
                ROOT / "outputs/phase5_run/relevance_audit_blinded.csv",
                ROOT / "outputs/phase5_run/relevance_audit_key.csv",
                output,
            )
            manifest = json.loads((output / "run_manifest.json").read_text())
            code_files = manifest["code_files"]
            self.assertIn("src/edu_recommender/label_audit/service.py", code_files)
            self.assertNotIn("src/edu_recommender/label_audit.py", code_files)
            self.assertTrue(all((ROOT / path).is_file() for path in code_files))

    def test_complete_audit_is_joined_and_summarised(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blinded, completed, key = self._write_fixture(root)
            result = analyse_author_audit(
                completed,
                blinded,
                key,
                root / "output",
            )

            self.assertEqual(result.item_count, 3)
            self.assertEqual(result.definite_count, 2)
            self.assertEqual(result.uncertain_count, 1)
            self.assertEqual(result.agreement_count, 1)
            self.assertEqual(result.disagreement_count, 1)
            self.assertEqual(result.agreement_rate, 0.5)
            self.assertTrue((root / "output/author_audit_summary.md").is_file())

    def test_changed_blinded_metadata_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blinded, completed, key = self._write_fixture(root)
            rows = self._read(completed)
            rows[0]["resource_title"] = "Changed title"
            self._write(completed, (*VISIBLE_COLUMNS, *REVIEW_COLUMNS), rows)

            with self.assertRaisesRegex(ValueError, "changed blinded metadata"):
                analyse_author_audit(
                    completed,
                    blinded,
                    key,
                    root / "output",
                )

    def test_low_confidence_without_notes_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blinded, completed, key = self._write_fixture(root)
            rows = self._read(completed)
            rows[0]["reviewer_confidence"] = "1"
            rows[0]["reviewer_notes"] = ""
            self._write(completed, (*VISIBLE_COLUMNS, *REVIEW_COLUMNS), rows)

            with self.assertRaisesRegex(ValueError, "requires reviewer_notes"):
                analyse_author_audit(
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
        base_rows = [
            cls._visible_row("A001", "Resource 1"),
            cls._visible_row("A002", "Resource 2"),
            cls._visible_row("A003", "Resource 3"),
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
                for row in base_rows
            ],
        )
        decisions = (("1", "3", ""), ("1", "2", ""), ("U", "1", "Ambiguous"))
        cls._write(
            completed,
            (*VISIBLE_COLUMNS, *REVIEW_COLUMNS),
            [
                {
                    **row,
                    "reviewer_relevance": decisions[index][0],
                    "reviewer_confidence": decisions[index][1],
                    "reviewer_notes": decisions[index][2],
                }
                for index, row in enumerate(base_rows)
            ],
        )
        cls._write(
            key,
            KEY_COLUMNS,
            [
                {
                    "audit_item_id": "A001",
                    "profile_id": "P001",
                    "resource_id": "R001",
                    "current_label": "1",
                    "selection_reason": "recommended_relevant",
                },
                {
                    "audit_item_id": "A002",
                    "profile_id": "P002",
                    "resource_id": "R002",
                    "current_label": "0",
                    "selection_reason": "recommended_not_relevant",
                },
                {
                    "audit_item_id": "A003",
                    "profile_id": "P003",
                    "resource_id": "R003",
                    "current_label": "1",
                    "selection_reason": "relevant_not_recommended",
                },
            ],
        )
        return blinded, completed, key

    @staticmethod
    def _visible_row(item_id: str, title: str) -> dict[str, str]:
        return {
            "audit_item_id": item_id,
            "pathway": "data_analyst",
            "profile_name": "Test learner",
            "target_pathway": "data_analyst",
            "current_skills": "sql:1",
            "weak_skills": "sql",
            "preferred_difficulty": "1",
            "resource_title": title,
            "provider": "Provider",
            "topic": "sql",
            "skills": "sql",
            "resource_difficulty": "1",
            "format": "course",
            "prerequisites": "",
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
