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

from generate_audit_review import generate_audit_review_html


class BrowserAuditReviewTests(unittest.TestCase):
    def test_generated_review_is_portable_complete_and_blinded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            general = temp_root / "general.csv"
            targeted = temp_root / "targeted.csv"
            output = temp_root / "audit_review.html"
            self._write_fixture(general, "A", 40)
            self._write_fixture(targeted, "H", 10)
            generate_audit_review_html(
                general,
                targeted,
                output,
            )
            html = output.read_text(encoding="utf-8")

        self.assertIn("Relevance judgement audit", html)
        self.assertIn('"audit_item_id":"A001"', html)
        self.assertIn('"audit_item_id":"H001"', html)
        self.assertEqual(html.count('"audit_item_id":"A'), 40)
        self.assertEqual(html.count('"audit_item_id":"H'), 10)
        self.assertNotIn('"current_label"', html)
        self.assertNotIn('"experiment_role"', html)
        self.assertNotIn('"profile_id"', html)
        self.assertNotIn('"resource_id"', html)
        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)

    @staticmethod
    def _write_fixture(path: Path, prefix: str, count: int) -> None:
        fieldnames = [
            "audit_item_id",
            "pathway",
            "profile_name",
            "target_pathway",
            "current_skills",
            "weak_skills",
            "preferred_difficulty",
            "resource_title",
            "provider",
            "topic",
            "skills",
            "resource_difficulty",
            "format",
            "prerequisites",
            "reviewer_relevance",
            "reviewer_confidence",
            "reviewer_notes",
        ]
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for index in range(1, count + 1):
                writer.writerow(
                    {
                        "audit_item_id": f"{prefix}{index:03d}",
                        "pathway": "data_analyst",
                        "profile_name": "Test learner",
                        "target_pathway": "data_analyst",
                        "current_skills": "sql:0",
                        "weak_skills": "sql",
                        "preferred_difficulty": "1",
                        "resource_title": f"Resource {index}",
                        "provider": "Test provider",
                        "topic": "sql",
                        "skills": "sql",
                        "resource_difficulty": "1",
                        "format": "course",
                        "prerequisites": "",
                        "reviewer_relevance": "",
                        "reviewer_confidence": "",
                        "reviewer_notes": "",
                    }
                )


if __name__ == "__main__":
    unittest.main()
