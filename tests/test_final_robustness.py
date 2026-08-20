from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from edu_recommender.data import GradedResourceSet, LearnerProfile, Resource
from edu_recommender.final_robustness.counterfactual import (
    _difficulty_cases,
    _irrelevant_topic_case,
    _prerequisite_cases,
)
from edu_recommender.final_robustness.label_sensitivity import (
    _scenario_relevance,
)
from edu_recommender.weak_skill_alignment_experiment import (
    ReadinessGatedWeakSkillAlignmentSuite,
)


class LabelSensitivityTests(unittest.TestCase):
    def test_scenarios_respect_bounds_and_do_not_mutate_canonical_grades(self) -> None:
        canonical = {
            "P001": GradedResourceSet(
                {"R001", "R002", "R003"},
                {"R001": 1, "R002": 2, "R003": 3},
            )
        }
        confidence = {
            ("P001", "R001"): 1,
            ("P001", "R002"): 2,
            ("P001", "R003"): 3,
        }

        down, down_count = _scenario_relevance(
            canonical,
            confidence,
            "all_uncertain_down_one",
        )
        up, up_count = _scenario_relevance(
            canonical,
            confidence,
            "all_uncertain_up_one",
        )

        self.assertEqual(down["P001"].grades, {"R001": 1, "R002": 1, "R003": 3})
        self.assertEqual(up["P001"].grades, {"R001": 2, "R002": 3, "R003": 3})
        self.assertEqual((down_count, up_count), (1, 2))
        self.assertEqual(
            canonical["P001"].grades,
            {"R001": 1, "R002": 2, "R003": 3},
        )


class CounterfactualInvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = LearnerProfile(
            profile_id="P001",
            name="Test learner",
            target_pathway="software_developer",
            current_skills={"python": 0, "testing": 0},
            completed_topics=set(),
            weak_skills={"testing"},
            preferred_difficulty=1,
            max_duration_hours=5.0,
            preferred_format="course",
        )
        self.resource = Resource(
            resource_id="R001",
            title="Testing with Python",
            provider="Provider",
            topic="testing",
            skills={"python", "testing"},
            difficulty_level=2,
            duration_hours=2.0,
            format="course",
            prerequisites={"python"},
            cost="free",
            popularity_score=0.8,
            quality_score=0.8,
            pathway_relevance={"software_developer": 3},
            description="Testing practice in Python.",
        )
        self.suite = ReadinessGatedWeakSkillAlignmentSuite(
            [self.resource],
            {"software_developer": {"python": 2, "testing": 3}},
        )

    def test_prerequisite_completion_and_difficulty_invariants_pass(self) -> None:
        prerequisite = _prerequisite_cases(
            self.suite,
            self.profile,
            [self.resource],
        )
        difficulty = _difficulty_cases(
            self.suite,
            self.profile,
            [self.resource],
        )

        self.assertEqual(len(prerequisite), 1)
        self.assertTrue(prerequisite[0]["passed"])
        self.assertEqual(prerequisite[0]["after_signal"], 1.0)
        self.assertEqual(len(difficulty), 1)
        self.assertTrue(difficulty[0]["passed"])

    def test_unknown_completed_topic_leaves_ranking_identical(self) -> None:
        row = _irrelevant_topic_case(self.suite, self.profile)
        self.assertTrue(row["passed"])


if __name__ == "__main__":
    unittest.main()
