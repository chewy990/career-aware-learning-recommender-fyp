"""Own authentication persistence for local SQLite and deployed Postgres."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from api.config import AUTH_DB_PATH, DATABASE_URL


class AuthConnection:
    """Expose the small DB-API subset used by authentication services."""

    def __init__(self, connection: Any, *, postgres: bool) -> None:
        self._connection = connection
        self._postgres = postgres

    def execute(self, statement: str, parameters: Sequence[object] = ()) -> Any:
        if self._postgres:
            statement = statement.replace("?", "%s")
        return self._connection.execute(statement, parameters)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()


def _database_url() -> str:
    """Read at connection time so tests and local shells can override it safely."""
    return os.getenv("DATABASE_URL", DATABASE_URL).strip()


def _postgres_connection(database_url: str) -> Any:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:  # pragma: no cover - exercised only when mis-deployed
        raise RuntimeError(
            "Postgres requires the psycopg package from requirements.txt"
        ) from exc
    return psycopg.connect(database_url, row_factory=dict_row)


def _open_connection() -> AuthConnection:
    database_url = _database_url()
    if database_url:
        return AuthConnection(_postgres_connection(database_url), postgres=True)

    AUTH_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(AUTH_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return AuthConnection(connection, postgres=False)


def _schema_statements(*, postgres: bool) -> tuple[str, ...]:
    created_at_type = "TIMESTAMPTZ" if postgres else "TEXT"
    return (
        f"""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_at {created_at_type} NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
        """
    CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        created_at DOUBLE PRECISION NOT NULL,
        last_seen_at DOUBLE PRECISION NOT NULL,
        expires_at DOUBLE PRECISION NOT NULL,
        FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
    )
    """,
        """
    CREATE TABLE IF NOT EXISTS login_failures (
        username TEXT NOT NULL,
        client_key TEXT NOT NULL,
        failed_at DOUBLE PRECISION NOT NULL
    )
    """,
        "CREATE INDEX IF NOT EXISTS idx_sessions_username ON sessions(username)",
        """
    CREATE INDEX IF NOT EXISTS idx_login_failures_lookup
    ON login_failures(username, client_key, failed_at)
    """,
    )

EXPECTED_COLUMNS = {
    "users": {"username", "password_hash", "salt", "created_at"},
    "sessions": {
        "token_hash",
        "username",
        "created_at",
        "last_seen_at",
        "expires_at",
    },
    "login_failures": {"username", "client_key", "failed_at"},
}


def initialize_auth_database() -> None:
    """Create the current authentication schema once at application startup."""
    with auth_connection() as connection:
        postgres = bool(_database_url())
        for statement in _schema_statements(postgres=postgres):
            connection.execute(statement)

        for table, expected in EXPECTED_COLUMNS.items():
            if postgres:
                rows = connection.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = ?
                    """,
                    (table,),
                ).fetchall()
                actual = {str(row["column_name"]) for row in rows}
            else:
                actual = {
                    str(row[1])
                    for row in connection.execute(f"PRAGMA table_info({table})")
                }
            if actual != expected:
                raise RuntimeError(
                    f"Unsupported auth schema for {table}; "
                    "use an empty deployment database or delete data/auth.sqlite3"
                )


@contextmanager
def auth_connection() -> Iterator[AuthConnection]:
    """Yield one request-scoped connection and always close it."""
    connection = _open_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def is_unique_violation(error: Exception) -> bool:
    """Recognise duplicate usernames without coupling routes to a DB driver."""
    if isinstance(error, sqlite3.IntegrityError):
        return True
    try:
        from psycopg.errors import UniqueViolation
    except ImportError:
        return False
    return isinstance(error, UniqueViolation)
