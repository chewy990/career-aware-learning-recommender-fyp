from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apply_graded_relevance import apply_completed_grades
from generate_graded_relevance_pack import VISIBLE_COLUMNS, generate_pack


class GradedRelevanceWorkflowTests(unittest.TestCase):
    def test_pack_is_complete_blinded_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first, first_key = generate_pack(Path(first_dir))
            second, second_key = generate_pack(Path(second_dir))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first_key.read_bytes(), second_key.read_bytes())
            with first.open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 258)
            self.assertEqual(tuple(rows[0]), VISIBLE_COLUMNS)
            self.assertNotIn("profile_id", rows[0])
            self.assertNotIn("resource_id", rows[0])
            self.assertNotIn("model", rows[0])
            self.assertNotIn("rank", rows[0])
            html = (Path(first_dir) / "graded_relevance_review.html").read_text(
                encoding="utf-8"
            )
            self.assertNotIn('"profile_id"', html)
            self.assertNotIn('"resource_id"', html)
            self.assertNotIn('"model"', html)
            self.assertNotIn('"rank"', html)
            self.assertIn("Save progress", html)
            self.assertIn("Download completed CSV", html)

    def test_completed_pack_applies_only_valid_human_grades(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            blinded, _ = generate_pack(temp_path / "pack")
            with blinded.open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
            for row in rows:
                row["relevance_grade"] = "2"
                row["reviewer_confidence"] = "3"
            completed = temp_path / "completed.csv"
            with completed.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=VISIBLE_COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            output = temp_path / "graded.csv"
            count = apply_completed_grades(completed, output, temp_path / "pack")
            self.assertEqual(count, 258)
            with output.open(encoding="utf-8", newline="") as file:
                applied = list(csv.DictReader(file))
            self.assertEqual(len(applied), 258)
            self.assertEqual(set(applied[0]), {"profile_id", "resource_id", "relevance_grade"})
            self.assertTrue(all(row["relevance_grade"] == "2" for row in applied))

    def test_browser_progress_backup_can_be_applied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            blinded, _ = generate_pack(temp_path / "pack")
            with blinded.open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
            pack_id = "graded-relevance-review-" + hashlib.sha256(
                blinded.read_bytes()
            ).hexdigest()[:16]
            backup = temp_path / "progress.json"
            backup.write_text(
                json.dumps(
                    {
                        "pack": pack_id,
                        "state": {
                            "answers": {
                                row["grading_item_id"]: {
                                    "grade": "3",
                                    "confidence": "2",
                                    "notes": "",
                                }
                                for row in rows
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            output = temp_path / "graded.csv"
            count = apply_completed_grades(backup, output, temp_path / "pack")
            self.assertEqual(count, 258)
            with output.open(encoding="utf-8", newline="") as file:
                applied = list(csv.DictReader(file))
            self.assertTrue(all(row["relevance_grade"] == "3" for row in applied))


if __name__ == "__main__":
    unittest.main()
