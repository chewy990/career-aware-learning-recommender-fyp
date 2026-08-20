from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import run_pipeline
from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.models import RecommenderSuite
from edu_recommender.validation import DataValidationError


class RecommendationDeterminismTests(unittest.TestCase):
    def test_hybrid_explanation_breaks_equal_gap_ties_alphabetically(self) -> None:
        skills = {"testing", "sql", "python", "apis"}
        resource = Resource(
            resource_id="R001",
            title="Practice resource",
            provider="Test provider",
            topic="project",
            skills=skills,
            difficulty_level=1,
            duration_hours=2.0,
            format="project",
            prerequisites=set(),
            cost="free",
            popularity_score=0.8,
            quality_score=0.8,
            pathway_relevance={"software_developer": 3},
            description="A deterministic test resource.",
        )
        profile = LearnerProfile(
            profile_id="P001",
            name="Test learner",
            target_pathway="software_developer",
            current_skills={skill: 0 for skill in skills},
            completed_topics=set(),
            weak_skills=set(),
            preferred_difficulty=1,
            max_duration_hours=5.0,
            preferred_format="project",
        )
        suite = RecommenderSuite(
            [resource],
            {"software_developer": {skill: 3 for skill in skills}},
        )

        recommendation = suite.recommend(profile, model="hybrid", top_k=1)[0]

        self.assertIn("skill gaps in apis, python, sql", recommendation.explanation)

    def test_equal_scores_use_resource_id_as_final_tie_breaker(self) -> None:
        profile = LearnerProfile(
            profile_id="P001",
            name="Test learner",
            target_pathway="data_analyst",
            current_skills={"sql": 0},
            completed_topics=set(),
            weak_skills={"sql"},
            preferred_difficulty=1,
            max_duration_hours=5.0,
            preferred_format="course",
        )
        resources = [self._resource("R002"), self._resource("R001")]
        suite = RecommenderSuite(resources, {"data_analyst": {"sql": 3}})

        recommendations = suite.recommend(profile, model="popularity", top_k=2)

        self.assertEqual([item.resource_id for item in recommendations], ["R001", "R002"])

    @staticmethod
    def _resource(resource_id: str) -> Resource:
        return Resource(
            resource_id=resource_id,
            title="Same title",
            provider="Test provider",
            topic="sql",
            skills={"sql"},
            difficulty_level=1,
            duration_hours=2.0,
            format="course",
            prerequisites=set(),
            cost="free",
            popularity_score=0.8,
            quality_score=0.8,
            pathway_relevance={"data_analyst": 3},
            description="Same description.",
        )


class PipelineReproducibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temporary_directory.name)
        self.data_dir = self.temp_root / "data"
        self.output_dir = self.temp_root / "outputs"
        shutil.copytree(ROOT / "data", self.data_dir)
        shutil.copytree(ROOT / "docs", self.temp_root / "docs")
        shutil.copytree(ROOT / "src", self.temp_root / "src")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_two_runs_have_identical_rankings_explanations_and_fingerprint(self) -> None:
        with (
            patch.object(run_pipeline, "DATA_DIR", self.data_dir),
            patch.object(run_pipeline, "OUTPUT_DIR", self.output_dir),
        ):
            run_pipeline.main()
            first_recommendations = (
                self.output_dir / "recommendations_hybrid.csv"
            ).read_bytes()
            first_report = (self.output_dir / "report.html").read_bytes()
            first_eda = (self.output_dir / "dataset_summary.csv").read_bytes()
            first_figure = (
                self.output_dir / "figures" / "resources_by_pathway.png"
            ).read_bytes()
            first_phase3_figure = (
                self.output_dir / "figures" / "phase3_metrics_by_k.png"
            ).read_bytes()
            first_uncertainty = (
                self.output_dir / "evaluation_uncertainty.csv"
            ).read_bytes()
            first_phase4_figure = (
                self.output_dir
                / "figures"
                / "phase4_ablation_ndcg_at_5.png"
            ).read_bytes()
            first_phase4_summary = (
                self.output_dir / "phase4_summary.md"
            ).read_bytes()
            first_phase5_figure = (
                self.output_dir
                / "figures"
                / "phase5_paired_ndcg_at_5.png"
            ).read_bytes()
            first_phase5_summary = (
                self.output_dir / "phase5_summary.md"
            ).read_bytes()
            first_audit = (
                self.output_dir / "relevance_audit_blinded.csv"
            ).read_bytes()
            first_prerequisite_figure = (
                self.output_dir
                / "figures"
                / "prerequisite_experiment_paired_ndcg_at_5.png"
            ).read_bytes()
            first_prerequisite_summary = (
                self.output_dir / "prerequisite_experiment_summary.md"
            ).read_bytes()
            first_prerequisite_recommendations = (
                self.output_dir
                / "prerequisite_experiment_recommendations.csv"
            ).read_bytes()
            first_prerequisite_audit = (
                self.output_dir
                / "prerequisite_experiment_audit_blinded.csv"
            ).read_bytes()
            first_manifest = json.loads(
                (self.output_dir / "run_manifest.json").read_text(encoding="utf-8")
            )

            run_pipeline.main()
            second_recommendations = (
                self.output_dir / "recommendations_hybrid.csv"
            ).read_bytes()
            second_report = (self.output_dir / "report.html").read_bytes()
            second_eda = (self.output_dir / "dataset_summary.csv").read_bytes()
            second_figure = (
                self.output_dir / "figures" / "resources_by_pathway.png"
            ).read_bytes()
            second_phase3_figure = (
                self.output_dir / "figures" / "phase3_metrics_by_k.png"
            ).read_bytes()
            second_uncertainty = (
                self.output_dir / "evaluation_uncertainty.csv"
            ).read_bytes()
            second_phase4_figure = (
                self.output_dir
                / "figures"
                / "phase4_ablation_ndcg_at_5.png"
            ).read_bytes()
            second_phase4_summary = (
                self.output_dir / "phase4_summary.md"
            ).read_bytes()
            second_phase5_figure = (
                self.output_dir
                / "figures"
                / "phase5_paired_ndcg_at_5.png"
            ).read_bytes()
            second_phase5_summary = (
                self.output_dir / "phase5_summary.md"
            ).read_bytes()
            second_audit = (
                self.output_dir / "relevance_audit_blinded.csv"
            ).read_bytes()
            second_prerequisite_figure = (
                self.output_dir
                / "figures"
                / "prerequisite_experiment_paired_ndcg_at_5.png"
            ).read_bytes()
            second_prerequisite_summary = (
                self.output_dir / "prerequisite_experiment_summary.md"
            ).read_bytes()
            second_prerequisite_recommendations = (
                self.output_dir
                / "prerequisite_experiment_recommendations.csv"
            ).read_bytes()
            second_prerequisite_audit = (
                self.output_dir
                / "prerequisite_experiment_audit_blinded.csv"
            ).read_bytes()
            second_manifest = json.loads(
                (self.output_dir / "run_manifest.json").read_text(encoding="utf-8")
            )

        self.assertEqual(first_recommendations, second_recommendations)
        self.assertEqual(first_report, second_report)
        self.assertEqual(first_eda, second_eda)
        self.assertEqual(first_figure, second_figure)
        self.assertEqual(first_phase3_figure, second_phase3_figure)
        self.assertEqual(first_uncertainty, second_uncertainty)
        self.assertEqual(first_phase4_figure, second_phase4_figure)
        self.assertEqual(first_phase4_summary, second_phase4_summary)
        self.assertEqual(first_phase5_figure, second_phase5_figure)
        self.assertEqual(first_phase5_summary, second_phase5_summary)
        self.assertEqual(first_audit, second_audit)
        self.assertEqual(
            first_prerequisite_figure,
            second_prerequisite_figure,
        )
        self.assertEqual(
            first_prerequisite_summary,
            second_prerequisite_summary,
        )
        self.assertEqual(
            first_prerequisite_recommendations,
            second_prerequisite_recommendations,
        )
        self.assertEqual(
            first_prerequisite_audit,
            second_prerequisite_audit,
        )
        self.assertEqual(
            first_manifest["configuration_fingerprint_sha256"],
            second_manifest["configuration_fingerprint_sha256"],
        )
        self.assertEqual(first_manifest["k_values"], [3, 5, 10])
        self.assertEqual(first_manifest["random_seed"], 42)
        self.assertEqual(first_manifest["eda_version"], 1)
        self.assertEqual(first_manifest["evaluation_version"], 2)
        self.assertEqual(first_manifest["robustness_version"], 1)
        self.assertEqual(first_manifest["statistical_comparison_version"], 1)
        self.assertEqual(first_manifest["prerequisite_experiment_version"], 1)
        self.assertEqual(first_manifest["bootstrap_replicates"], 10_000)
        self.assertEqual(first_manifest["seeded_configuration_count"], 12)
        self.assertEqual(first_manifest["planned_paired_comparisons"], 18)
        self.assertEqual(first_manifest["audit_items_per_pathway"], 8)
        self.assertEqual(first_manifest["prerequisite_experiment_primary_k"], 5)
        self.assertEqual(first_manifest["input_files"]["resources.csv"]["rows"], 96)
        self.assertIn("src/edu_recommender/validation/__init__.py", first_manifest["code_files"])
        self.assertEqual(
            second_manifest["output_files"]["recommendations_hybrid.csv"]["sha256"],
            hashlib.sha256(second_recommendations).hexdigest(),
        )
        self.assertEqual(
            second_manifest["output_files"][
                "figures/resources_by_pathway.png"
            ]["sha256"],
            hashlib.sha256(second_figure).hexdigest(),
        )
        self.assertEqual(
            second_manifest["output_files"][
                "figures/phase3_metrics_by_k.png"
            ]["sha256"],
            hashlib.sha256(second_phase3_figure).hexdigest(),
        )
        self.assertEqual(
            second_manifest["output_files"][
                "figures/phase4_ablation_ndcg_at_5.png"
            ]["sha256"],
            hashlib.sha256(second_phase4_figure).hexdigest(),
        )
        self.assertEqual(
            second_manifest["output_files"][
                "figures/phase5_paired_ndcg_at_5.png"
            ]["sha256"],
            hashlib.sha256(second_phase5_figure).hexdigest(),
        )
        self.assertEqual(
            second_manifest["output_files"][
                "relevance_audit_blinded.csv"
            ]["sha256"],
            hashlib.sha256(second_audit).hexdigest(),
        )
        self.assertEqual(
            second_manifest["output_files"][
                "figures/prerequisite_experiment_paired_ndcg_at_5.png"
            ]["sha256"],
            hashlib.sha256(second_prerequisite_figure).hexdigest(),
        )
        self.assertEqual(
            second_manifest["output_files"][
                "prerequisite_experiment_recommendations.csv"
            ]["sha256"],
            hashlib.sha256(
                second_prerequisite_recommendations
            ).hexdigest(),
        )
        self.assertEqual(
            second_manifest["output_files"][
                "prerequisite_experiment_audit_blinded.csv"
            ]["sha256"],
            hashlib.sha256(second_prerequisite_audit).hexdigest(),
        )

    def test_pipeline_stops_before_outputs_when_validation_fails(self) -> None:
        resources_path = self.data_dir / "resources.csv"
        invalid_text = resources_path.read_text(encoding="utf-8").replace(
            ",course,",
            ",invalid_format,",
            1,
        )
        resources_path.write_text(invalid_text, encoding="utf-8")

        with (
            patch.object(run_pipeline, "DATA_DIR", self.data_dir),
            patch.object(run_pipeline, "OUTPUT_DIR", self.output_dir),
            self.assertRaises(DataValidationError),
        ):
            run_pipeline.main()

        self.assertFalse(self.output_dir.exists())


if __name__ == "__main__":
    unittest.main()
