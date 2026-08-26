"""Enforce the documented source-size and dependency architecture."""

from __future__ import annotations

import ast
import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

STRUCTURE_DOC = ROOT / "docs" / "code_structure.md"
SOURCE_ROOTS = (SRC, ROOT / "frontend" / "src", ROOT / "tests")
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".css"}
LINE_TARGET = 300
LINE_LIMIT = 350


def maintained_source_files() -> list[Path]:
    """Return maintained code files while excluding generated dependencies."""
    files = [
        path
        for source_root in SOURCE_ROOTS
        for path in source_root.rglob("*")
        if path.is_file()
        and path.suffix in SOURCE_SUFFIXES
        and not {"node_modules", "dist", "__pycache__"} & set(path.parts)
    ]
    return sorted(set(files))


def imported_modules(path: Path) -> set[str]:
    """Return Python import names used for static dependency checks."""
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


class SourceSizeTests(unittest.TestCase):
    def test_maintained_source_files_stay_within_ceiling(self) -> None:
        oversized = {
            path.relative_to(ROOT).as_posix(): len(
                path.read_text(encoding="utf-8-sig").splitlines()
            )
            for path in maintained_source_files()
            if len(path.read_text(encoding="utf-8-sig").splitlines()) > LINE_LIMIT
        }
        self.assertEqual(oversized, {})

    def test_soft_limit_exceptions_have_documented_justification(self) -> None:
        documentation = STRUCTURE_DOC.read_text(encoding="utf-8")
        undocumented = []
        for path in maintained_source_files():
            line_count = len(path.read_text(encoding="utf-8-sig").splitlines())
            if LINE_TARGET < line_count <= LINE_LIMIT:
                relative = path.relative_to(ROOT).as_posix()
                if f"`{relative}`" not in documentation:
                    undocumented.append((relative, line_count))
        self.assertEqual(undocumented, [])


class DependencyBoundaryTests(unittest.TestCase):
    def test_retired_interface_is_absent_from_maintained_source(self) -> None:
        offenders = [
            path.relative_to(ROOT).as_posix()
            for path in (*SRC.rglob("*"), *(ROOT / "frontend" / "src").rglob("*"))
            if path.is_file()
            and path.suffix in SOURCE_SUFFIXES
            and "streamlit" in path.read_text(encoding="utf-8-sig").casefold()
        ]
        self.assertEqual(offenders, [])


class PublicPackageTests(unittest.TestCase):
    def test_scientific_package_reexports_remain_available(self) -> None:
        expected = {
            "edu_recommender.validation": "validate_data_dir",
            "edu_recommender.eda": "generate_eda",
            "edu_recommender.evaluation": "generate_evaluation",
            "edu_recommender.robustness": "generate_robustness_analysis",
            "edu_recommender.statistical_comparison": (
                "generate_statistical_comparison"
            ),
            "edu_recommender.prerequisite_experiment": (
                "generate_prerequisite_experiment"
            ),
            "edu_recommender.label_audit": "analyse_author_audit",
            "edu_recommender.learning_path": "build_learning_path",
            "edu_recommender.models": "RecommenderSuite",
        }
        missing = [
            f"{module_name}.{attribute}"
            for module_name, attribute in expected.items()
            if not hasattr(importlib.import_module(module_name), attribute)
        ]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
