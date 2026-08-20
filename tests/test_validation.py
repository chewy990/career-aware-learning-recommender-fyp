from __future__ import annotations

import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from edu_recommender.validation import DataValidationError, validate_data_dir


class DataValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temporary_directory.name)
        self.data_dir = self.temp_root / "data"
        shutil.copytree(ROOT / "data", self.data_dir)
        shutil.copytree(ROOT / "docs", self.temp_root / "docs")
        shutil.copytree(ROOT / "src", self.temp_root / "src")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_current_datasets_pass_with_expected_counts(self) -> None:
        summary = validate_data_dir(self.data_dir)

        self.assertEqual(summary.row_counts["resources.csv"], 96)
        self.assertEqual(summary.row_counts["resource_modules.csv"], 40)
        self.assertEqual(summary.row_counts["skill_map.csv"], 16)
        self.assertEqual(summary.row_counts["learner_profiles.csv"], 11)
        self.assertEqual(summary.row_counts["relevance_judgements.csv"], 11)
        self.assertEqual(summary.row_counts["skill_sources.csv"], 10)
        self.assertTrue(all(row["status"] == "passed" for row in summary.checks))

    def test_learning_links_target_specific_resources(self) -> None:
        broad_urls = {
            "https://www.kaggle.com/learn",
            "https://www.freecodecamp.org/learn",
            "https://www.storytellingwithdata.com/",
        }
        broad_module_urls = {
            "https://openrefine.org/docs",
            "https://www.freecodecamp.org/learn/back-end-development-and-apis",
            "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures-v8",
            "https://www.freecodecamp.org/learn/relational-database",
        }
        for filename in ("resources.csv", "resource_modules.csv"):
            _, rows = self._read_rows(filename)
            for row in rows:
                with self.subTest(filename=filename, row=row):
                    url = row["source_url"].strip()
                    parsed = urlparse(url)
                    self.assertNotIn(url.rstrip("/"), {item.rstrip("/") for item in broad_urls})
                    if filename == "resource_modules.csv":
                        self.assertNotIn(
                            url.rstrip("/"),
                            {item.rstrip("/") for item in broad_module_urls},
                        )
                    self.assertNotIn("search", parsed.path.casefold())
                    self.assertNotIn("search", parsed.query.casefold())

    def test_optional_graded_labels_must_cover_every_binary_positive(self) -> None:
        _, judgement_rows = self._read_rows("relevance_judgements.csv")
        graded_rows = [
            {
                "profile_id": row["profile_id"],
                "resource_id": resource_id,
                "relevance_grade": "2",
            }
            for row in judgement_rows
            for resource_id in row["relevant_resource_ids"].split(";")
        ]
        self._write_rows(
            "relevance_judgements_graded.csv",
            ["profile_id", "resource_id", "relevance_grade"],
            graded_rows,
        )
        summary = validate_data_dir(self.data_dir)
        self.assertEqual(
            summary.row_counts["relevance_judgements_graded.csv"],
            len(graded_rows),
        )

        graded_rows[0]["relevance_grade"] = "4"
        graded_rows.pop()
        self._write_rows(
            "relevance_judgements_graded.csv",
            ["profile_id", "resource_id", "relevance_grade"],
            graded_rows,
        )
        with self.assertRaises(DataValidationError) as context:
            validate_data_dir(self.data_dir)
        self.assertIn("outside the allowed range 1 to 3", str(context.exception))
        self.assertIn("missing grade for positive judgement", str(context.exception))

    def test_reports_ids_categories_ranges_and_broken_references_together(self) -> None:
        self._update_row(
            "resources.csv",
            0,
            {
                "resource_id": "R002",
                "format": "podcast",
                "popularity_score": "1.2",
                "prerequisites": "unknown_skill",
            },
        )
        self._update_row(
            "resource_modules.csv",
            0,
            {"parent_resource_id": "R999"},
        )
        self._update_row(
            "learner_profiles.csv",
            0,
            {
                "target_pathway": "data_wizard",
                "current_skills": "sql:4",
            },
        )
        self._update_row(
            "relevance_judgements.csv",
            0,
            {"relevant_resource_ids": "R001;R999"},
        )

        with self.assertRaises(DataValidationError) as context:
            validate_data_dir(self.data_dir)

        message = str(context.exception)
        self.assertIn("duplicate ID 'R002'", message)
        self.assertIn("invalid category 'podcast'", message)
        self.assertIn("outside the allowed range 0 to 1", message)
        self.assertIn("unknown value(s): unknown_skill", message)
        self.assertIn("unknown resource ID 'R999'", message)
        self.assertIn("invalid category 'data_wizard'", message)
        self.assertIn("level for 'sql' must be between 0 and 3", message)
        self.assertIn(
            "[relevant_resource_ids]: unknown resource ID(s): R001, R999",
            message,
        )

    def test_requires_positive_and_negative_examples_for_every_profile(self) -> None:
        resource_ids = [
            row["resource_id"] for row in self._read_rows("resources.csv")[1]
        ]
        self._update_row(
            "relevance_judgements.csv",
            0,
            {"relevant_resource_ids": ";".join(resource_ids)},
        )
        self._update_row(
            "relevance_judgements.csv",
            1,
            {"relevant_resource_ids": ""},
        )

        with self.assertRaises(DataValidationError) as context:
            validate_data_dir(self.data_dir)

        message = str(context.exception)
        self.assertIn("evaluation profile has no negative examples", message)
        self.assertIn("evaluation profile has no positive examples", message)

    def test_reports_missing_columns_and_local_source_files(self) -> None:
        fieldnames, rows = self._read_rows("resources.csv")
        fieldnames.remove("quality_score")
        for row in rows:
            row.pop("quality_score")
        self._write_rows("resources.csv", fieldnames, rows)
        self._update_row(
            "skill_sources.csv",
            0,
            {"url": "docs/does-not-exist.md"},
        )

        with self.assertRaises(DataValidationError) as context:
            validate_data_dir(self.data_dir)

        message = str(context.exception)
        self.assertIn("missing required column(s): quality_score", message)
        self.assertIn("local reference does not exist", message)

    def test_rejects_unknown_pathway_columns(self) -> None:
        fieldnames, rows = self._read_rows("skill_map.csv")
        fieldnames.append("data_wizard")
        for row in rows:
            row["data_wizard"] = "1"
        self._write_rows("skill_map.csv", fieldnames, rows)

        with self.assertRaises(DataValidationError) as context:
            validate_data_dir(self.data_dir)

        self.assertIn(
            "unknown pathway column(s): data_wizard",
            str(context.exception),
        )

    def _update_row(
        self,
        filename: str,
        row_index: int,
        updates: dict[str, str],
    ) -> None:
        fieldnames, rows = self._read_rows(filename)
        rows[row_index].update(updates)
        self._write_rows(filename, fieldnames, rows)

    def _read_rows(self, filename: str) -> tuple[list[str], list[dict[str, str]]]:
        with (self.data_dir / filename).open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader.fieldnames or []), list(reader)

    def _write_rows(
        self,
        filename: str,
        fieldnames: list[str],
        rows: list[dict[str, str]],
    ) -> None:
        with (self.data_dir / filename).open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
