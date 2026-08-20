from __future__ import annotations

import sys
import unittest
from collections import Counter
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
from edu_recommender.models import RecommenderSuite
from edu_recommender.statistical_comparison import (
    AUDIT_ITEMS_PER_PATHWAY,
    build_label_audit_sample,
    effect_magnitude,
    exact_paired_permutation_test,
    exact_wilcoxon_signed_rank_test,
    holm_adjust,
)


class PairedStatisticalTestTests(unittest.TestCase):
    def test_exact_sign_flip_permutation_uses_all_assignments(self) -> None:
        self.assertEqual(
            exact_paired_permutation_test([1.0, 1.0]),
            0.5,
        )
        self.assertEqual(
            exact_paired_permutation_test([1.0] * 11),
            2 / (2**11),
        )
        self.assertEqual(
            exact_paired_permutation_test([0.0, 0.0]),
            1.0,
        )

    def test_exact_wilcoxon_handles_ties_and_zero_differences(self) -> None:
        w_plus, p_value = exact_wilcoxon_signed_rank_test([1.0, 1.0])
        self.assertEqual(w_plus, 3.0)
        self.assertEqual(p_value, 0.5)
        self.assertEqual(
            exact_wilcoxon_signed_rank_test([0.0, 0.0]),
            (0.0, 1.0),
        )

    def test_holm_adjustment_is_monotonic_in_sorted_order(self) -> None:
        adjusted = holm_adjust([0.01, 0.04, 0.03])
        self.assertEqual(adjusted, [0.03, 0.06, 0.06])

    def test_effect_magnitude_uses_predeclared_thresholds(self) -> None:
        self.assertEqual(effect_magnitude(0.19), "negligible")
        self.assertEqual(effect_magnitude(-0.2), "small")
        self.assertEqual(effect_magnitude(0.5), "medium")
        self.assertEqual(effect_magnitude(-0.8), "large")


class BlindedLabelAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data_dir = ROOT / "data"
        cls.resources = read_resources(data_dir / "resources.csv")
        cls.profiles = read_profiles(data_dir / "learner_profiles.csv")
        cls.relevance = read_relevance_judgements(
            data_dir / "relevance_judgements.csv"
        )
        skill_map = read_skill_map(data_dir / "skill_map.csv")
        suite = RecommenderSuite(cls.resources, skill_map)
        cls.hybrid_recommendations = {
            profile.profile_id: suite.recommend(
                profile,
                model="hybrid",
                top_k=10,
            )
            for profile in cls.profiles
        }

    def test_audit_is_deterministic_balanced_and_blinded(self) -> None:
        first_blinded, first_key = build_label_audit_sample(
            self.hybrid_recommendations,
            self.profiles,
            self.resources,
            self.relevance,
            random_seed=42,
        )
        second_blinded, second_key = build_label_audit_sample(
            self.hybrid_recommendations,
            self.profiles,
            self.resources,
            self.relevance,
            random_seed=42,
        )

        self.assertEqual(first_blinded, second_blinded)
        self.assertEqual(first_key, second_key)
        pathway_count = len(
            {profile.target_pathway for profile in self.profiles}
        )
        self.assertEqual(
            len(first_blinded),
            pathway_count * AUDIT_ITEMS_PER_PATHWAY,
        )
        self.assertEqual(
            set(Counter(row["pathway"] for row in first_blinded).values()),
            {AUDIT_ITEMS_PER_PATHWAY},
        )
        self.assertTrue(
            all(
                row["reviewer_relevance"] == ""
                and row["reviewer_confidence"] == ""
                and row["reviewer_notes"] == ""
                for row in first_blinded
            )
        )
        self.assertNotIn("current_label", first_blinded[0])
        self.assertNotIn("resource_id", first_blinded[0])
        self.assertNotIn("profile_id", first_blinded[0])
        self.assertIn("current_label", first_key[0])

    def test_audit_key_covers_all_four_planned_case_types(self) -> None:
        _, key_rows = build_label_audit_sample(
            self.hybrid_recommendations,
            self.profiles,
            self.resources,
            self.relevance,
            random_seed=42,
        )

        reasons = {str(row["selection_reason"]) for row in key_rows}
        self.assertTrue(
            {
                "recommended_relevant",
                "recommended_not_relevant",
                "relevant_not_recommended",
                "not_relevant_not_recommended",
            }.issubset(reasons)
        )


if __name__ == "__main__":
    unittest.main()
