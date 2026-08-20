from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from edu_recommender.data import GradedResourceSet, LearnerProfile, Resource
from edu_recommender.evaluation import (
    bootstrap_mean_confidence_interval,
    build_diagnostic_profile_rows,
    build_metric_summary_rows,
    build_profile_metric_rows,
    difficulty_match_rate,
    intra_list_diversity,
    ndcg_at_k,
    precision_at_k,
    prerequisite_validity_rate,
    recall_at_k,
    skill_gap_coverage,
)
from edu_recommender.models import Recommendation


class RankingMetricTests(unittest.TestCase):
    def test_precision_recall_and_ndcg_have_known_values(self) -> None:
        ranked = ["R1", "R2", "R3"]
        relevant = {"R1", "R3", "R4", "R5"}

        self.assertAlmostEqual(precision_at_k(ranked, relevant, 3), 2 / 3)
        self.assertAlmostEqual(recall_at_k(ranked, relevant, 3), 0.5)
        expected_dcg = 1 + 1 / math.log2(4)
        expected_ideal = 1 + 1 / math.log2(3) + 1 / math.log2(4)
        self.assertAlmostEqual(
            ndcg_at_k(ranked, relevant, 3),
            expected_dcg / expected_ideal,
        )

    def test_metrics_handle_empty_relevance_and_short_lists(self) -> None:
        self.assertEqual(precision_at_k(["R1"], {"R1"}, 3), 1 / 3)
        self.assertEqual(recall_at_k(["R1"], set(), 3), 0.0)
        self.assertEqual(ndcg_at_k(["R1"], set(), 3), 0.0)
        self.assertEqual(precision_at_k(["R1"], {"R1"}, 0), 0.0)
        self.assertEqual(ndcg_at_k(["R1"], {"R1"}, 0), 0.0)

    def test_ndcg_uses_graded_gain_when_grades_are_available(self) -> None:
        relevant = GradedResourceSet(
            {"R1", "R2", "R3"},
            {"R1": 3, "R2": 2, "R3": 1},
        )

        self.assertEqual(ndcg_at_k(["R1", "R2", "R3"], relevant, 3), 1.0)
        reversed_score = ndcg_at_k(["R3", "R2", "R1"], relevant, 3)
        self.assertGreater(reversed_score, 0.0)
        self.assertLess(reversed_score, 1.0)
        self.assertEqual(precision_at_k(["R1", "R2", "R3"], relevant, 3), 1.0)
        self.assertEqual(recall_at_k(["R1", "R2", "R3"], relevant, 3), 1.0)

    def test_summary_is_traceable_to_profile_rows(self) -> None:
        profiles = [
            self._profile("P1", "data_analyst"),
            self._profile("P2", "software_developer"),
        ]
        recommendations = {
            "hybrid": {
                "P1": [
                    self._recommendation("P1", "R1", 1),
                    self._recommendation("P1", "R2", 2),
                ],
                "P2": [
                    self._recommendation("P2", "R2", 1),
                    self._recommendation("P2", "R3", 2),
                ],
            }
        }
        relevance = {"P1": {"R1"}, "P2": {"R3"}}

        profile_rows = build_profile_metric_rows(
            recommendations,
            relevance,
            profiles,
            (1, 2),
        )
        summary_rows = build_metric_summary_rows(profile_rows)
        k2 = next(row for row in summary_rows if int(row["k"]) == 2)
        profile_k2 = [
            float(row["precision_at_k"])
            for row in profile_rows
            if int(row["k"]) == 2
        ]

        self.assertEqual(k2["profile_count"], 2)
        self.assertEqual(k2["precision_at_k"], round(sum(profile_k2) / 2, 4))
        self.assertEqual(k2["precision_at_k"], 0.5)

    def test_seeded_bootstrap_is_deterministic(self) -> None:
        values = [0.2, 0.4, 0.8, 1.0]
        first = bootstrap_mean_confidence_interval(
            values,
            seed=42,
            replicates=2_000,
        )
        second = bootstrap_mean_confidence_interval(
            values,
            seed=42,
            replicates=2_000,
        )

        self.assertEqual(first, second)
        self.assertLessEqual(first[0], sum(values) / len(values))
        self.assertGreaterEqual(first[1], sum(values) / len(values))
        self.assertEqual(
            bootstrap_mean_confidence_interval(
                [0.75, 0.75],
                seed=42,
                replicates=100,
            ),
            (0.75, 0.75),
        )

    @staticmethod
    def _profile(profile_id: str, pathway: str) -> LearnerProfile:
        return LearnerProfile(
            profile_id=profile_id,
            name=profile_id,
            target_pathway=pathway,
            current_skills={"sql": 1},
            completed_topics=set(),
            weak_skills={"python"},
            preferred_difficulty=2,
            max_duration_hours=8.0,
            preferred_format="course",
        )

    @staticmethod
    def _recommendation(
        profile_id: str,
        resource_id: str,
        rank: int,
    ) -> Recommendation:
        return Recommendation(
            profile_id=profile_id,
            model="hybrid",
            rank=rank,
            resource_id=resource_id,
            title=resource_id,
            provider="Provider",
            score=1.0,
            explanation="Test",
        )


class RecommendationDiagnosticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = LearnerProfile(
            profile_id="P1",
            name="Learner",
            target_pathway="data_analyst",
            current_skills={"sql": 1},
            completed_topics=set(),
            weak_skills={"python"},
            preferred_difficulty=2,
            max_duration_hours=8.0,
            preferred_format="course",
        )
        self.resources = [
            self._resource(
                "R1",
                "Provider A",
                "course",
                {"sql"},
                1,
                set(),
            ),
            self._resource(
                "R2",
                "Provider B",
                "project",
                {"python"},
                3,
                {"sql"},
            ),
        ]

    def test_quality_diagnostics_have_known_values(self) -> None:
        gaps = {"sql": 0.75, "python": 0.25}

        self.assertEqual(skill_gap_coverage(self.resources, gaps), 1.0)
        self.assertEqual(intra_list_diversity(self.resources), 1.0)
        self.assertEqual(difficulty_match_rate(self.resources, self.profile), 1.0)
        self.assertEqual(
            prerequisite_validity_rate(self.resources, self.profile),
            1.0,
        )

    def test_profile_diagnostic_row_reconciles_to_recommendations(self) -> None:
        recommendations = {
            "hybrid": {
                "P1": [
                    Recommendation(
                        profile_id="P1",
                        model="hybrid",
                        rank=index + 1,
                        resource_id=resource.resource_id,
                        title=resource.title,
                        provider=resource.provider,
                        score=1.0,
                        explanation="Test",
                    )
                    for index, resource in enumerate(self.resources)
                ]
            }
        }

        rows = build_diagnostic_profile_rows(
            recommendations,
            [self.profile],
            self.resources,
            {"P1": {"sql": 0.75, "python": 0.25}},
            (2,),
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["distinct_provider_count"], 2)
        self.assertEqual(rows[0]["provider_diversity"], 1.0)
        self.assertEqual(rows[0]["distinct_format_count"], 2)
        self.assertEqual(rows[0]["format_diversity"], 1.0)
        self.assertEqual(rows[0]["skill_gap_coverage"], 1.0)

    @staticmethod
    def _resource(
        resource_id: str,
        provider: str,
        format_name: str,
        skills: set[str],
        difficulty: int,
        prerequisites: set[str],
    ) -> Resource:
        return Resource(
            resource_id=resource_id,
            title=resource_id,
            provider=provider,
            topic="test",
            skills=skills,
            difficulty_level=difficulty,
            duration_hours=2.0,
            format=format_name,
            prerequisites=prerequisites,
            cost="free",
            popularity_score=0.8,
            quality_score=0.8,
            pathway_relevance={"data_analyst": 3},
            description="Test",
        )


if __name__ == "__main__":
    unittest.main()
