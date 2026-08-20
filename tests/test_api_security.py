from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from api import main
from api.auth import storage, validation
from api.config import MAX_REQUEST_BODY_BYTES
from api.rate_limit import _TokenBucketLimiter, reset_rate_limits


class ApiSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_rate_limits()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "auth.sqlite3"
        self.path_patch = patch.object(storage, "AUTH_DB_PATH", self.database_path)
        self.path_patch.start()
        self.client_context = TestClient(main.app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.path_patch.stop()
        self.temporary_directory.cleanup()
        reset_rate_limits()

    def test_oversized_body_is_rejected_before_parsing(self) -> None:
        response = self.client.post(
            "/api/auth/register",
            headers={
                "Content-Type": "application/json",
                "Origin": "http://127.0.0.1:5173",
            },
            content=b"x" * (MAX_REQUEST_BODY_BYTES + 1),
        )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json(), {"detail": "Request body is too large"})

    def test_production_origin_policy_rejects_missing_origin(self) -> None:
        with patch.object(validation, "AUTH_REQUIRE_ORIGIN", True):
            response = self.client.post(
                "/api/auth/register",
                json={"username": "origin_user", "password": "correct horse battery"},
            )

        self.assertEqual(response.status_code, 403)

    def test_research_computation_requires_a_session(self) -> None:
        self.assertEqual(self.client.get("/api/research/metrics").status_code, 401)
        response = self.client.post(
            "/api/research/recommendations",
            headers={"Origin": "http://127.0.0.1:5173"},
            json={"profile_id": "P001", "model": "hybrid", "top_k": 5},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            self.client.get("/api/research/dataset-summary").status_code,
            200,
        )

    def test_authenticated_research_and_known_skill_validation(self) -> None:
        origin = {"Origin": "http://127.0.0.1:5173"}
        response = self.client.post(
            "/api/auth/register",
            headers=origin,
            json={"username": "research_user", "password": "correct horse battery"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get("/api/research/metrics").status_code, 200)
        response = self.client.post(
            "/api/research/recommendations",
            headers=origin,
            json={"profile_id": "P001", "model": "hybrid", "top_k": 5},
        )
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.post(
            "/api/learning-path",
            headers=origin,
            json={
                "target_pathway": "data_analyst",
                "current_skills": {"invented_skill": 1},
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_production_disables_docs_and_sets_hsts(self) -> None:
        with (
            patch.object(main, "IS_PRODUCTION", True),
            patch.object(main, "initialize_auth_database"),
        ):
            production_app = main.create_app()
            with TestClient(production_app) as client:
                self.assertEqual(client.get("/docs").status_code, 404)
                self.assertEqual(client.get("/openapi.json").status_code, 404)
                response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["strict-transport-security"],
            "max-age=31536000; includeSubDomains",
        )

    def test_token_bucket_returns_retry_after_when_exhausted(self) -> None:
        limiter = _TokenBucketLimiter()
        limiter.enforce("test", "client", capacity=1, window_seconds=60)

        with self.assertRaises(HTTPException) as raised:
            limiter.enforce("test", "client", capacity=1, window_seconds=60)

        self.assertEqual(raised.exception.status_code, 429)
        self.assertEqual(raised.exception.headers, {"Retry-After": "60"})


if __name__ == "__main__":
    unittest.main()
