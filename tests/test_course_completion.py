"""Check generated-course completion is distinct from pathway mastery."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from api.learning_service import course_complete


class CourseCompletionTests(unittest.TestCase):
    """Cover the completion flag returned with a generated course."""

    def test_all_actionable_items_complete_finishes_the_course(self) -> None:
        items = [
            {"can_improve": True, "completed": True},
            {"can_improve": False, "completed": False},
        ]
        self.assertTrue(course_complete(items))

    def test_an_unfinished_actionable_item_keeps_the_course_open(self) -> None:
        items = [{"can_improve": True, "completed": False}]
        self.assertFalse(course_complete(items))

    def test_a_course_without_actionable_items_is_not_complete(self) -> None:
        items = [{"can_improve": False, "completed": True}]
        self.assertFalse(course_complete(items))


if __name__ == "__main__":
    unittest.main()
