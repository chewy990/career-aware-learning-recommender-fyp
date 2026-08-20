"""Check pathway progression is computed from the skill map rather than hard-coded."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from edu_recommender.data import read_skill_map
from edu_recommender.progression import (
    next_pathways,
    pathway_coverage,
    pathway_overlap,
    remaining_skills,
)

SKILL_MAP = {
    "analyst": {"sql": 3, "statistics": 3, "machine_learning": 1},
    "scientist": {"sql": 2, "statistics": 3, "machine_learning": 3},
    "empty": {"sql": 0, "statistics": 0, "machine_learning": 0},
}


class ProgressionTests(unittest.TestCase):
    """Cover the arithmetic and the ordering guarantees."""

    def test_remaining_reports_only_shortfalls(self) -> None:
        remaining = remaining_skills(SKILL_MAP, "scientist", SKILL_MAP["analyst"])
        self.assertEqual(remaining, {"machine_learning": 2})

    def test_remaining_is_empty_when_requirements_are_met(self) -> None:
        met = {"sql": 3, "statistics": 3, "machine_learning": 3}
        self.assertEqual(remaining_skills(SKILL_MAP, "scientist", met), {})

    def test_coverage_is_the_share_of_requirement_already_held(self) -> None:
        # scientist requires 8 levels in total and 2 are missing
        self.assertAlmostEqual(
            pathway_coverage(SKILL_MAP, "scientist", SKILL_MAP["analyst"]),
            1 - 2 / 8,
        )

    def test_coverage_of_a_pathway_with_no_requirement_is_zero(self) -> None:
        self.assertEqual(pathway_coverage(SKILL_MAP, "empty", {}), 0.0)

    def test_overlap_is_directional(self) -> None:
        overlap = pathway_overlap(SKILL_MAP)
        self.assertNotEqual(
            overlap["analyst"]["scientist"],
            overlap["scientist"]["analyst"],
        )

    def test_next_pathways_excludes_the_current_one(self) -> None:
        options = next_pathways(
            SKILL_MAP,
            SKILL_MAP["analyst"],
            exclude=("analyst",),
            limit=0,
        )
        self.assertNotIn("analyst", [option["pathway"] for option in options])

    def test_pathways_the_learner_already_has_are_excluded(self) -> None:
        """Offering an existing course would lead somewhere with nothing to do."""

        skill_map = read_skill_map(ROOT / "data" / "skill_map.csv")
        held = ("data_analyst", "data_scientist")
        options = next_pathways(
            skill_map,
            skill_map["data_analyst"],
            exclude=held,
            limit=0,
        )
        offered = [option["pathway"] for option in options]
        for pathway in held:
            self.assertNotIn(pathway, offered)
        self.assertEqual(len(offered), len(skill_map) - len(held))

    def test_a_completed_course_stays_excluded_after_it_is_removed(self) -> None:
        """Course completion is permanent, so removal must not re-offer it."""

        skill_map = read_skill_map(ROOT / "data" / "skill_map.csv")
        # the learner removed the Data Analyst course but had completed it
        held, completed = ("data_scientist",), ("data_analyst",)
        options = next_pathways(
            skill_map,
            skill_map["data_analyst"],
            exclude=(*held, *completed),
            limit=0,
        )
        self.assertNotIn("data_analyst", [option["pathway"] for option in options])

    def test_next_pathways_ranks_by_coverage_then_name(self) -> None:
        skill_map = dict(SKILL_MAP)
        skill_map["duplicate"] = dict(SKILL_MAP["scientist"])
        options = next_pathways(skill_map, SKILL_MAP["analyst"], limit=0)
        keys = [(-round(float(o["coverage"]), 6), o["pathway"]) for o in options]
        self.assertEqual(keys, sorted(keys))

    def test_pathway_with_no_requirement_is_never_offered(self) -> None:
        options = next_pathways(SKILL_MAP, SKILL_MAP["analyst"], limit=0)
        self.assertNotIn("empty", [option["pathway"] for option in options])

    def test_no_pathway_pair_is_privileged_in_the_project_data(self) -> None:
        """Every pathway must offer suggestions, not only Data Analyst."""

        skill_map = read_skill_map(ROOT / "data" / "skill_map.csv")
        for pathway in skill_map:
            options = next_pathways(
                skill_map,
                skill_map[pathway],
                exclude=(pathway,),
            )
            self.assertTrue(options, f"{pathway} produced no next pathway")

    def test_coverage_reflects_skills_gained_rather_than_starting_skills(self) -> None:
        """The completion view must not report the learner's pre-course position.

        A learner who starts at zero and is shown coverage computed from those
        starting skills sees 0% and every skill listed as outstanding, which is
        what a stale path snapshot produced before the value was recomputed on
        each completion.

        """

        skill_map = read_skill_map(ROOT / "data" / "skill_map.csv")
        starting = pathway_coverage(skill_map, "data_scientist", {})
        finished = pathway_coverage(
            skill_map,
            "data_scientist",
            skill_map["data_analyst"],
        )
        self.assertEqual(starting, 0.0)
        self.assertGreater(finished, starting)

    def test_project_data_reproduces_the_reported_analyst_figure(self) -> None:
        skill_map = read_skill_map(ROOT / "data" / "skill_map.csv")
        coverage = pathway_coverage(
            skill_map,
            "data_scientist",
            skill_map["data_analyst"],
        )
        self.assertEqual(round(coverage, 2), 0.74)


if __name__ == "__main__":
    unittest.main()
