from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE_ENTRY = ROOT / "frontend" / "src" / "styles.css"
STYLE_DIRECTORY = STYLE_ENTRY.parent / "styles"

EXPECTED_IMPORTS = [
    "foundation-tokens-reset.css",
    "foundation-controls.css",
    "foundation-navigation.css",
    "foundation-courses.css",
    "foundation-research.css",
    "design-system.css",
    "landing-shell.css",
    "landing-schematic.css",
    "landing-sections.css",
    "about.css",
    "product-layout.css",
    "product-courses.css",
    "product-next-pathways.css",
    "product-confirm.css",
    "product-forms.css",
    "product-research-responsive.css",
    "typography.css",
    "account-menu.css",
    "dashboard.css",
    "auth.css",
    "research-evidence.css",
    "research-evaluation.css",
]


class FrontendStylesheetTests(unittest.TestCase):
    def test_feature_stylesheets_are_imported_in_cascade_order(self) -> None:
        expected = [
            f'@import "./styles/{filename}";'
            for filename in EXPECTED_IMPORTS
        ]
        actual = STYLE_ENTRY.read_text(encoding="utf-8").splitlines()

        self.assertEqual(actual, expected)

    def test_each_imported_stylesheet_exists_and_contains_rules(self) -> None:
        for filename in EXPECTED_IMPORTS:
            with self.subTest(filename=filename):
                content = (STYLE_DIRECTORY / filename).read_text(
                    encoding="utf-8"
                )
                self.assertTrue(content.strip())
                self.assertNotIn("@import", content)
                self.assertIn("{", content)
                self.assertIn("}", content)


if __name__ == "__main__":
    unittest.main()
