"""Create, rotate, and clear authenticated browser sessions.

Raw tokens exist only long enough to set HttpOnly cookies. This module must not
validate passwords or define HTTP routes.
"""

from __future__ import annotations

import secrets
import time

from fastapi import Response

from api.auth.security import token_digest
from api.auth.storage import auth_connection
from api.config import (
    AUTH_COOKIE_NAME,
    AUTH_COOKIE_SAMESITE,
    AUTH_COOKIE_SECURE,
    SESSION_ABSOLUTE_SECONDS,
    SESSION_IDLE_SECONDS,
)


def create_session_token(username: str) -> str:
    """Create a bounded session and persist only its SHA-256 digest."""
    token = secrets.token_urlsafe(32)
    now = time.time()
    with auth_connection() as connection:
        connection.execute(
            "DELETE FROM sessions WHERE expires_at <= ? OR last_seen_at <= ?",
            (now, now - SESSION_IDLE_SECONDS),
        )
        connection.execute(
            """
            INSERT INTO sessions
                (token_hash, username, created_at, last_seen_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (token_digest(token), username, now, now, now + SESSION_ABSOLUTE_SECONDS),
        )
        # Limit stolen-session exposure without changing the public auth API.
        connection.execute(
            """
            DELETE FROM sessions
            WHERE token_hash IN (
                SELECT token_hash FROM (
                    SELECT
                        token_hash,
                        ROW_NUMBER() OVER (ORDER BY created_at DESC) AS session_rank
                    FROM sessions
                    WHERE username = ?
                ) ranked_sessions
                WHERE session_rank > 5
            )
            """,
            (username,),
        )
    return token


def set_session_cookie(response: Response, token: str) -> None:
    """Set the strict, HttpOnly browser credential."""
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=SESSION_ABSOLUTE_SECONDS,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Remove the browser credential using the same cookie attributes."""
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE,
        path="/",
    )


def establish_session(username: str, response: Response) -> dict[str, object]:
    """Create a session and return the unchanged authentication response."""
    set_session_cookie(response, create_session_token(username))
    return {
        "username": username,
        "session_expires_in_seconds": SESSION_ABSOLUTE_SECONDS,
    }
