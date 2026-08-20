from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.models import RecommenderSuite
from edu_recommender.weak_skill_alignment_experiment import (
    GATED_VARIANT_MODEL,
    VARIANT_MODEL,
    ReadinessGatedWeakSkillAlignmentSuite,
    WeakSkillAlignmentSuite,
    build_gated_variant_recommendations,
    build_variant_recommendations,
)


class WeakSkillAlignmentExperimentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resources = [
            self._resource("R001", {"sql"}),
            self._resource("R002", {"testing"}),
        ]
        self.profile = LearnerProfile(
            profile_id="P001",
            name="Test learner",
            target_pathway="software_developer",
            current_skills={"sql": 0, "testing": 0},
            completed_topics=set(),
            weak_skills={"testing"},
            preferred_difficulty=1,
            max_duration_hours=5.0,
            preferred_format="course",
        )
        self.skill_map = {
            "software_developer": {"sql": 3, "testing": 3},
        }

    def test_variant_aligns_only_to_remaining_declared_weak_skills(self) -> None:
        baseline = RecommenderSuite(self.resources, self.skill_map)
        variant = WeakSkillAlignmentSuite(self.resources, self.skill_map)

        baseline_sql = baseline.hybrid_score_details(
            self.profile,
            self.resources[0],
        )
        variant_sql = variant.hybrid_score_details(
            self.profile,
            self.resources[0],
        )
        variant_testing = variant.hybrid_score_details(
            self.profile,
            self.resources[1],
        )

        self.assertEqual(
            baseline_sql.raw_signals["job_skill_alignment"],
            0.5,
        )
        self.assertEqual(
            variant_sql.raw_signals["job_skill_alignment"],
            0.0,
        )
        self.assertEqual(
            variant_testing.raw_signals["job_skill_alignment"],
            1.0,
        )

    def test_variant_labels_rankings_without_mutating_default_model(self) -> None:
        baseline_suite = RecommenderSuite(self.resources, self.skill_map)
        variant_suite = WeakSkillAlignmentSuite(self.resources, self.skill_map)

        baseline_before = baseline_suite.recommend(
            self.profile,
            model="hybrid",
            top_k=2,
        )
        variant = build_variant_recommendations(
            variant_suite,
            [self.profile],
            top_k=2,
        )[self.profile.profile_id]
        baseline_after = baseline_suite.recommend(
            self.profile,
            model="hybrid",
            top_k=2,
        )

        self.assertEqual(baseline_before, baseline_after)
        self.assertTrue(all(item.model == VARIANT_MODEL for item in variant))
        self.assertEqual(variant[0].resource_id, "R002")

    def test_readiness_gate_multiplies_weak_alignment_by_existing_signals(self) -> None:
        difficult_resource = Resource(
            **{
                **self.resources[1].__dict__,
                "difficulty_level": 2,
                "prerequisites": {"testing"},
            }
        )
        gated = ReadinessGatedWeakSkillAlignmentSuite(
            [self.resources[0], difficult_resource],
            self.skill_map,
        )

        details = gated.hybrid_score_details(
            self.profile,
            difficult_resource,
        )
        recommendations = build_gated_variant_recommendations(
            gated,
            [self.profile],
            top_k=2,
        )[self.profile.profile_id]

        self.assertEqual(details.raw_signals["difficulty_match"], 0.5)
        self.assertEqual(details.raw_signals["prerequisite_match"], 0.0)
        self.assertEqual(details.raw_signals["job_skill_alignment"], 0.0)
        self.assertTrue(
            all(item.model == GATED_VARIANT_MODEL for item in recommendations)
        )

    @staticmethod
    def _resource(resource_id: str, skills: set[str]) -> Resource:
        return Resource(
            resource_id=resource_id,
            title=f"Resource {resource_id}",
            provider="Provider",
            topic=next(iter(skills)),
            skills=skills,
            difficulty_level=1,
            duration_hours=2.0,
            format="course",
            prerequisites=set(),
            cost="free",
            popularity_score=0.8,
            quality_score=0.8,
            pathway_relevance={"software_developer": 3},
            description="Test resource.",
        )


if __name__ == "__main__":
    unittest.main()
