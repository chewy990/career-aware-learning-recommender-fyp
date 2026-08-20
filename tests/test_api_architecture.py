from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from api.main import app


class ApiArchitectureTests(unittest.TestCase):
    def test_all_public_routes_are_registered(self) -> None:
        expected_paths = {
            "/api/auth/change-password",
            "/api/auth/login",
            "/api/auth/logout",
            "/api/auth/me",
            "/api/auth/register",
            "/api/complete-item",
            "/api/health",
            "/api/learning-path",
            "/api/next-pathways",
            "/api/pathways",
            "/api/profiles",
            "/api/research/dataset-summary",
            "/api/research/metrics",
            "/api/research/recommendations",
        }

        self.assertEqual(set(app.openapi()["paths"]), expected_paths)

    def test_api_import_loads_only_the_maintained_application(self) -> None:
        command = "from api.main import app; assert app is not None"
        result = subprocess.run(
            [sys.executable, "-c", command],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(SRC)},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr or result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
