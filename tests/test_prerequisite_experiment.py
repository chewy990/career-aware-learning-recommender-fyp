from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from edu_recommender.data import (
    LearnerProfile,
    Resource,
    read_profiles,
    read_relevance_judgements,
    read_resources,
    read_skill_map,
)
from edu_recommender.evaluation import build_profile_metric_rows
from edu_recommender.models import (
    RecommenderSuite,
    prerequisites_satisfied,
)
from edu_recommender.prerequisite_experiment import (
    VARIANT_MODEL,
    build_eligible_recommendations,
    build_profile_change_rows,
    build_targeted_audit,
)


class HardPrerequisiteEligibilityTests(unittest.TestCase):
    def test_filter_excludes_ineligible_candidate_and_refills_list(self) -> None:
        resources = [
            self._resource("R001", quality=1.0, prerequisites={"python"}),
            self._resource("R002", quality=0.8),
            self._resource("R003", quality=0.7),
        ]
        profile = LearnerProfile(
            profile_id="P001",
            name="Test learner",
            target_pathway="data_analyst",
            current_skills={"sql": 1, "python": 0},
            completed_topics=set(),
            weak_skills={"sql"},
            preferred_difficulty=1,
            max_duration_hours=5.0,
            preferred_format="course",
        )
        suite = RecommenderSuite(
            resources,
            {"data_analyst": {"sql": 3, "python": 2}},
        )

        baseline = suite.recommend(
            profile,
            model="popularity",
            top_k=2,
        )
        filtered = suite.recommend(
            profile,
            model="popularity",
            top_k=2,
            enforce_prerequisites=True,
        )

        self.assertEqual(
            [item.resource_id for item in baseline],
            ["R001", "R002"],
        )
        self.assertEqual(
            [item.resource_id for item in filtered],
            ["R002", "R003"],
        )

    def test_default_recommendation_behavior_is_unchanged(self) -> None:
        resources = [
            self._resource("R001", quality=1.0, prerequisites={"python"}),
            self._resource("R002", quality=0.8),
        ]
        profile = LearnerProfile(
            profile_id="P001",
            name="Test learner",
            target_pathway="data_analyst",
            current_skills={"sql": 1},
            completed_topics=set(),
            weak_skills={"sql"},
            preferred_difficulty=1,
            max_duration_hours=5.0,
            preferred_format="course",
        )
        suite = RecommenderSuite(
            resources,
            {"data_analyst": {"sql": 3, "python": 2}},
        )

        implicit = suite.recommend(profile, model="hybrid", top_k=2)
        explicit = suite.recommend(
            profile,
            model="hybrid",
            top_k=2,
            enforce_prerequisites=False,
        )

        self.assertEqual(implicit, explicit)

    def test_real_variant_is_deterministic_complete_and_eligible(self) -> None:
        data_dir = ROOT / "data"
        resources = read_resources(data_dir / "resources.csv")
        profiles = read_profiles(data_dir / "learner_profiles.csv")
        suite = RecommenderSuite(
            resources,
            read_skill_map(data_dir / "skill_map.csv"),
        )
        resource_lookup = {
            resource.resource_id: resource
            for resource in resources
        }

        first = build_eligible_recommendations(suite, profiles, top_k=10)
        second = build_eligible_recommendations(suite, profiles, top_k=10)

        self.assertEqual(first, second)
        for profile in profiles:
            recommendations = first[profile.profile_id]
            self.assertEqual(len(recommendations), 10)
            self.assertTrue(
                all(
                    item.model == VARIANT_MODEL
                    and prerequisites_satisfied(
                        profile,
                        resource_lookup[item.resource_id],
                    )
                    for item in recommendations
                )
            )

    def test_targeted_audit_is_blinded_and_covers_changed_top_five(self) -> None:
        data_dir = ROOT / "data"
        resources = read_resources(data_dir / "resources.csv")
        profiles = read_profiles(data_dir / "learner_profiles.csv")
        relevance = read_relevance_judgements(
            data_dir / "relevance_judgements.csv"
        )
        suite = RecommenderSuite(
            resources,
            read_skill_map(data_dir / "skill_map.csv"),
        )
        baseline = {
            profile.profile_id: suite.recommend(
                profile,
                model="hybrid",
                top_k=10,
            )
            for profile in profiles
        }
        variant = build_eligible_recommendations(
            suite,
            profiles,
            top_k=10,
        )
        profile_rows = build_profile_metric_rows(
            {"hybrid": baseline, VARIANT_MODEL: variant},
            relevance,
            profiles,
            (3, 5, 10),
        )
        change_rows = build_profile_change_rows(
            baseline,
            variant,
            profiles,
            resources,
            relevance,
            profile_rows,
            10,
        )

        blinded, key = build_targeted_audit(
            change_rows,
            profiles,
            resources,
            relevance,
            random_seed=42,
        )

        self.assertEqual(len(blinded), 10)
        self.assertEqual(
            {row["experiment_role"] for row in key},
            {"baseline_removed", "variant_replacement"},
        )
        self.assertEqual(
            sum(row["experiment_role"] == "baseline_removed" for row in key),
            5,
        )
        self.assertTrue(
            all(
                row["reviewer_relevance"] == ""
                and row["reviewer_confidence"] == ""
                and row["reviewer_notes"] == ""
                for row in blinded
            )
        )
        self.assertNotIn("current_label", blinded[0])
        self.assertNotIn("experiment_role", blinded[0])
        self.assertNotIn("resource_id", blinded[0])

    @staticmethod
    def _resource(
        resource_id: str,
        quality: float,
        prerequisites: set[str] | None = None,
    ) -> Resource:
        return Resource(
            resource_id=resource_id,
            title=f"Resource {resource_id}",
            provider="Test provider",
            topic="sql",
            skills={"sql"},
            difficulty_level=1,
            duration_hours=2.0,
            format="course",
            prerequisites=prerequisites or set(),
            cost="free",
            popularity_score=quality,
            quality_score=quality,
            pathway_relevance={"data_analyst": 3},
            description="A test resource.",
        )


if __name__ == "__main__":
    unittest.main()
