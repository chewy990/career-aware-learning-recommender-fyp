from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from api.auth import storage
from api.main import app
from api.rate_limit import reset_rate_limits


class FakePostgresResult:
    def __init__(self, rows: list[dict[str, str]] | None = None) -> None:
        self.rows = rows or []

    def fetchall(self) -> list[dict[str, str]]:
        return self.rows


class FakePostgresConnection:
    def __init__(self) -> None:
        self.executions: list[tuple[str, tuple[object, ...]]] = []
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def execute(
        self,
        statement: str,
        parameters: tuple[object, ...] = (),
    ) -> FakePostgresResult:
        self.executions.append((statement, parameters))
        if "information_schema.columns" in statement:
            table = str(parameters[0])
            return FakePostgresResult(
                [{"column_name": column} for column in storage.EXPECTED_COLUMNS[table]]
            )
        return FakePostgresResult()

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


class PostgresStorageTests(unittest.TestCase):
    def test_initialization_uses_postgres_schema_and_parameter_style(self) -> None:
        raw_connection = FakePostgresConnection()
        database_url = "postgresql://test.invalid/auth"

        with (
            patch.dict("os.environ", {"DATABASE_URL": database_url}),
            patch.object(
                storage,
                "_postgres_connection",
                return_value=raw_connection,
            ) as connect,
        ):
            storage.initialize_auth_database()

        connect.assert_called_once_with(database_url)
        self.assertTrue(raw_connection.committed)
        self.assertFalse(raw_connection.rolled_back)
        self.assertTrue(raw_connection.closed)

        statements = [statement for statement, _ in raw_connection.executions]
        self.assertIn("TIMESTAMPTZ", statements[0])
        schema_queries = [
            (statement, parameters)
            for statement, parameters in raw_connection.executions
            if "information_schema.columns" in statement
        ]
        self.assertEqual(len(schema_queries), len(storage.EXPECTED_COLUMNS))
        self.assertTrue(all("table_name = %s" in statement for statement, _ in schema_queries))
        self.assertEqual(
            {str(parameters[0]) for _, parameters in schema_queries},
            set(storage.EXPECTED_COLUMNS),
        )

    def test_postgres_connection_rolls_back_and_closes_after_error(self) -> None:
        raw_connection = FakePostgresConnection()

        with (
            patch.dict("os.environ", {"DATABASE_URL": "postgresql://test.invalid/auth"}),
            patch.object(storage, "_postgres_connection", return_value=raw_connection),
            self.assertRaisesRegex(RuntimeError, "database write failed"),
            storage.auth_connection() as connection,
        ):
            connection.execute(
                "INSERT INTO users (username) VALUES (?)",
                ("demo",),
            )
            raise RuntimeError("database write failed")

        self.assertEqual(
            raw_connection.executions[0],
            ("INSERT INTO users (username) VALUES (%s)", ("demo",)),
        )
        self.assertFalse(raw_connection.committed)
        self.assertTrue(raw_connection.rolled_back)
        self.assertTrue(raw_connection.closed)

    def test_postgres_driver_receives_dictionary_row_factory(self) -> None:
        raw_connection = Mock()
        database_url = "postgresql://test.invalid/auth"

        with patch("psycopg.connect", return_value=raw_connection) as connect:
            result = storage._postgres_connection(database_url)

        from psycopg.rows import dict_row

        self.assertIs(result, raw_connection)
        connect.assert_called_once_with(database_url, row_factory=dict_row)


class AuthenticationRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_rate_limits()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "auth.sqlite3"
        self.path_patch = patch.object(storage, "AUTH_DB_PATH", self.database_path)
        self.path_patch.start()
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.path_patch.stop()
        self.temporary_directory.cleanup()
        reset_rate_limits()

    def test_current_schema_and_complete_auth_lifecycle(self) -> None:
        connection = sqlite3.connect(self.database_path)
        try:
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(users)").fetchall()
            }
        finally:
            connection.close()
        self.assertEqual(
            columns,
            {"username", "password_hash", "salt", "created_at"},
        )

        response = self.client.post(
            "/api/auth/register",
            headers={"Origin": "http://127.0.0.1:5173"},
            json={"username": "audit_user", "password": "correct horse battery"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("HttpOnly", response.headers["set-cookie"])
        self.assertIn("SameSite=strict", response.headers["set-cookie"])
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)

        response = self.client.post(
            "/api/auth/change-password",
            headers={"Origin": "http://127.0.0.1:5173"},
            json={
                "current_password": "correct horse battery",
                "new_password": "a new correct horse battery",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            self.client.post(
                "/api/auth/logout",
                headers={"Origin": "http://127.0.0.1:5173"},
            ).status_code,
            200,
        )
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.assertEqual(
            self.client.post(
                "/api/auth/login",
                headers={"Origin": "http://127.0.0.1:5173"},
                json={"username": "audit_user", "password": "correct horse battery"},
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.post(
                "/api/auth/login",
                headers={"Origin": "http://127.0.0.1:5173"},
                json={
                    "username": "audit_user",
                    "password": "a new correct horse battery",
                },
            ).status_code,
            200,
        )

    def test_write_requests_reject_untrusted_or_removed_fields(self) -> None:
        self.assertEqual(
            self.client.post(
                "/api/auth/register",
                headers={"Origin": "http://127.0.0.1:5173"},
                json={"username": "schema_user", "password": "current schema password"},
            ).status_code,
            200,
        )
        response = self.client.post(
            "/api/learning-path",
            json={
                "target_pathway": "data_analyst",
                "current_skills": {"sql": 8},
                "max_duration_hours": 2,
            },
        )
        self.assertEqual(response.status_code, 422)

        response = self.client.post(
            "/api/research/recommendations",
            json={"profile_id": "P001", "model": "unknown", "top_k": 1000},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
