from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from edu_recommender.data import (
    read_profiles,
    read_resources,
    read_skill_map,
)
from edu_recommender.models import HYBRID_WEIGHTS, RecommenderSuite
from edu_recommender.robustness import (
    COMPONENTS,
    SEEDED_MULTIPLIER_RANGE,
    build_seeded_weight_configurations,
)


class HybridRobustnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data_dir = ROOT / "data"
        cls.resources = read_resources(data_dir / "resources.csv")
        cls.profiles = read_profiles(data_dir / "learner_profiles.csv")
        cls.skill_map = read_skill_map(data_dir / "skill_map.csv")

    def test_explicit_default_weights_preserve_rankings(self) -> None:
        default_suite = RecommenderSuite(self.resources, self.skill_map)
        explicit_suite = RecommenderSuite(
            self.resources,
            self.skill_map,
            hybrid_weights=HYBRID_WEIGHTS,
        )
        for profile in self.profiles:
            default_ids = [
                item.resource_id
                for item in default_suite.recommend(
                    profile,
                    model="hybrid",
                    top_k=10,
                )
            ]
            explicit_ids = [
                item.resource_id
                for item in explicit_suite.recommend(
                    profile,
                    model="hybrid",
                    top_k=10,
                )
            ]
            self.assertEqual(default_ids, explicit_ids)

    def test_component_contributions_reconcile_to_pipeline_score(self) -> None:
        suite = RecommenderSuite(self.resources, self.skill_map)
        profile = self.profiles[0]
        recommendation = suite.recommend(
            profile,
            model="hybrid",
            top_k=1,
        )[0]
        resource = next(
            resource
            for resource in self.resources
            if resource.resource_id == recommendation.resource_id
        )
        details = suite.hybrid_score_details(profile, resource)

        self.assertEqual(set(details.raw_signals), set(COMPONENTS))
        self.assertEqual(
            set(details.weighted_contributions),
            set(COMPONENTS),
        )
        self.assertAlmostEqual(
            sum(details.weighted_contributions.values()),
            details.total_score,
        )
        self.assertEqual(round(details.total_score, 4), recommendation.score)

    def test_zero_weight_removes_only_that_weighted_contribution(self) -> None:
        profile = self.profiles[0]
        resource = self.resources[0]
        default_details = RecommenderSuite(
            self.resources,
            self.skill_map,
        ).hybrid_score_details(profile, resource)
        ablated_details = RecommenderSuite(
            self.resources,
            self.skill_map,
            hybrid_weights={"career_relevance": 0.0},
        ).hybrid_score_details(profile, resource)

        self.assertEqual(
            default_details.raw_signals,
            ablated_details.raw_signals,
        )
        self.assertEqual(
            ablated_details.weighted_contributions["career_relevance"],
            0.0,
        )
        for component in COMPONENTS:
            if component != "career_relevance":
                self.assertAlmostEqual(
                    default_details.weighted_contributions[component],
                    ablated_details.weighted_contributions[component],
                )

    def test_seeded_weight_configurations_are_bounded_and_reproducible(self) -> None:
        first = build_seeded_weight_configurations(42, count=4)
        second = build_seeded_weight_configurations(42, count=4)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 5)
        self.assertEqual(first[0][0], "S000_baseline")
        for _, multipliers, weights in first[1:]:
            self.assertEqual(set(multipliers), set(COMPONENTS))
            self.assertEqual(set(weights), set(COMPONENTS))
            self.assertTrue(
                all(
                    SEEDED_MULTIPLIER_RANGE[0]
                    <= multiplier
                    <= SEEDED_MULTIPLIER_RANGE[1]
                    for multiplier in multipliers.values()
                )
            )

    def test_unknown_hybrid_weight_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown hybrid weight"):
            RecommenderSuite(
                self.resources,
                self.skill_map,
                hybrid_weights={"unknown_component": 1.0},
            )


if __name__ == "__main__":
    unittest.main()
