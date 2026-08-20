from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from edu_recommender.data import (
    read_profiles,
    read_relevance_judgements,
    read_resources,
    read_skill_map,
)
from edu_recommender.eda import build_eda_tables, generate_eda
from edu_recommender.validation import validate_data_dir


class ExploratoryDataAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data_dir = ROOT / "data"
        cls.validation = validate_data_dir(cls.data_dir)
        cls.resources = read_resources(cls.data_dir / "resources.csv")
        cls.profiles = read_profiles(cls.data_dir / "learner_profiles.csv")
        cls.relevance = read_relevance_judgements(
            cls.data_dir / "relevance_judgements.csv"
        )
        cls.skill_map = read_skill_map(cls.data_dir / "skill_map.csv")
        cls.tables = build_eda_tables(
            cls.resources,
            cls.profiles,
            cls.relevance,
            cls.skill_map,
            cls.validation.row_counts,
        )

    def test_catalogue_distributions_reconcile_to_96_resources(self) -> None:
        rows = self.tables["resource_distribution.csv"]
        for dimension in ("provider", "format", "difficulty", "duration_band", "cost"):
            total = sum(
                int(row["count"])
                for row in rows
                if row["dimension"] == dimension
            )
            self.assertEqual(total, 96, dimension)

        lookup = {
            (str(row["dimension"]), str(row["category"])): int(row["count"])
            for row in rows
        }
        self.assertEqual(lookup[("provider", "DataCamp")], 24)
        self.assertEqual(lookup[("format", "course")], 41)
        self.assertEqual(lookup[("difficulty", "Advanced")], 15)
        self.assertEqual(lookup[("cost", "free")], 47)
        self.assertEqual(lookup[("cost", "paid")], 49)
        self.assertEqual(
            lookup[("pathway_positive_relevance", "data_analyst")],
            55,
        )

    def test_required_pathway_skills_have_nonzero_catalogue_coverage(self) -> None:
        coverage = self.tables["pathway_skill_coverage.csv"]

        self.assertTrue(coverage)
        self.assertTrue(
            all(int(row["required_level"]) > 0 for row in coverage)
        )
        self.assertTrue(
            all(int(row["resources_covering_skill"]) > 0 for row in coverage)
        )
        self.assertNotIn(
            "no_coverage",
            {str(row["coverage_status"]) for row in coverage},
        )

    def test_profile_and_relevance_summaries_match_fixed_evaluation_set(self) -> None:
        profile_rows = self.tables["profile_distribution.csv"]
        pathway_counts = {
            str(row["category"]): int(row["count"])
            for row in profile_rows
            if row["dimension"] == "target_pathway"
        }
        self.assertEqual(pathway_counts["data_analyst"], 3)
        self.assertEqual(
            {
                count
                for pathway, count in pathway_counts.items()
                if pathway != "data_analyst"
            },
            {2},
        )

        relevant_counts = [
            int(row["relevant_count"])
            for row in self.tables["relevance_summary.csv"]
        ]
        # Sizes reflect the 31 July 2026 relevance-label revision, which added
        # R003 to P001 and P007, R048 to P003, R055 to P006, and removed R039
        # from P011. P011 was the previous maximum at 30.
        self.assertEqual(min(relevant_counts), 16)
        self.assertEqual(max(relevant_counts), 29)
        self.assertAlmostEqual(sum(relevant_counts) / len(relevant_counts), 23.45, places=2)

    def test_generated_tables_and_figures_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            first = generate_eda(
                self.resources,
                self.profiles,
                self.relevance,
                self.skill_map,
                self.validation.row_counts,
                output_dir,
            )
            first_hashes = {
                filename: hashlib.sha256((output_dir / filename).read_bytes()).hexdigest()
                for filename in first.output_files
            }

            second = generate_eda(
                self.resources,
                self.profiles,
                self.relevance,
                self.skill_map,
                self.validation.row_counts,
                output_dir,
            )
            second_hashes = {
                filename: hashlib.sha256((output_dir / filename).read_bytes()).hexdigest()
                for filename in second.output_files
            }

        self.assertEqual(first_hashes, second_hashes)
        self.assertEqual(len(first.output_files), 21)
        self.assertTrue(
            first_hashes["figures/resources_by_pathway.png"]
        )


if __name__ == "__main__":
    unittest.main()
