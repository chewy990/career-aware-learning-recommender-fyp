"""Resolve authenticated users for FastAPI dependencies.

This module validates and refreshes sessions. It must not inspect passwords or
define route handlers.
"""

from __future__ import annotations

import time

from fastapi import Cookie, HTTPException

from api.auth.security import token_digest
from api.auth.storage import auth_connection
from api.config import AUTH_COOKIE_NAME, SESSION_IDLE_SECONDS


def require_user(
    session_token: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
) -> str:
    """Return the session username or raise the existing 401 responses."""
    if not session_token or len(session_token) > 200:
        raise HTTPException(status_code=401, detail="Not logged in")

    now = time.time()
    digest = token_digest(session_token)
    with auth_connection() as connection:
        row = connection.execute(
            """
            SELECT username, last_seen_at, expires_at
            FROM sessions WHERE token_hash = ?
            """,
            (digest,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Session expired")
    if (
        float(row["expires_at"]) <= now
        or float(row["last_seen_at"]) <= now - SESSION_IDLE_SECONDS
    ):
        with auth_connection() as connection:
            connection.execute("DELETE FROM sessions WHERE token_hash = ?", (digest,))
        raise HTTPException(status_code=401, detail="Session expired")
    # Avoid a database write on every request while preserving idle expiry.
    if float(row["last_seen_at"]) <= now - 60:
        with auth_connection() as connection:
            connection.execute(
                "UPDATE sessions SET last_seen_at = ? WHERE token_hash = ?",
                (now, digest),
            )
    return str(row["username"])
