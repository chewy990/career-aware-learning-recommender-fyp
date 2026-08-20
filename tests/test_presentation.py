from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from edu_recommender.data import Resource, ResourceModule
from edu_recommender.presentation import (
    difficulty_label,
    display_pathway,
    display_skill,
    display_skill_list,
    skill_level_label,
    source_url_for_item,
)


class PresentationTests(unittest.TestCase):
    def test_labels_are_human_readable_and_deterministic(self) -> None:
        self.assertEqual(display_pathway("ml_engineer"), "ML Engineer")
        self.assertEqual(display_skill("oop"), "Object-oriented programming")
        self.assertEqual(display_skill_list({"sql", "apis"}), "APIs, SQL")
        self.assertEqual(skill_level_label(2), "Working knowledge")
        self.assertEqual(difficulty_label(1), "Beginner")

    def test_source_url_prefers_module_then_resource_without_search_fallback(self) -> None:
        resource = self._resource("https://resource.example")
        module = ResourceModule(
            module_id="M001",
            parent_resource_id=resource.resource_id,
            module_title="Module",
            provider="Provider",
            skills={"sql"},
            difficulty_level=1,
            duration_hours=1.0,
            source_url="https://module.example",
            date_checked="2026-07-31",
        )
        self.assertEqual(
            source_url_for_item(resource, module),
            "https://module.example",
        )
        self.assertEqual(
            source_url_for_item(resource, None),
            "https://resource.example",
        )
        self.assertEqual(source_url_for_item(self._resource(""), None), "")

    @staticmethod
    def _resource(source_url: str) -> Resource:
        return Resource(
            resource_id="R001",
            title="Unknown resource",
            provider="Unknown provider",
            topic="sql",
            skills={"sql"},
            difficulty_level=1,
            duration_hours=1.0,
            format="course",
            prerequisites=set(),
            cost="free",
            popularity_score=0.5,
            quality_score=0.5,
            pathway_relevance={"data_analyst": 1},
            description="Test",
            source_url=source_url,
            date_checked="2026-07-31" if source_url else "",
        )


if __name__ == "__main__":
    unittest.main()
