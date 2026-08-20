"""Validate authentication requests and enforce login throttling.

This module contains policy checks only. It must not create sessions or return
successful HTTP responses.
"""

from __future__ import annotations

import math
from typing import Any

from fastapi import HTTPException, Request

from api.config import (
    ALLOWED_ORIGINS,
    AUTH_REQUIRE_ORIGIN,
    COMMON_PASSWORDS,
    LOGIN_MAX_FAILURES,
    LOGIN_WINDOW_SECONDS,
    PASSWORD_MIN_LENGTH,
    USERNAME_PATTERN,
)


def validate_request_origin(request: Request) -> None:
    """Reject browser writes from origins outside the configured allow-list."""
    origin = request.headers.get("origin")
    if not origin and AUTH_REQUIRE_ORIGIN:
        raise HTTPException(status_code=403, detail="Request origin is required")
    if origin and origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="Request origin is not allowed")


def validate_registration_username(username: str) -> None:
    """Apply the canonical username syntax used by the prototype."""
    if not USERNAME_PATTERN.fullmatch(username):
        raise HTTPException(
            status_code=400,
            detail=(
                "Use 3-40 lowercase letters, numbers, dots, hyphens, "
                "or underscores"
            ),
        )


def validate_new_password(username: str, password: str) -> None:
    """Apply minimum-length and basic weak-password checks."""
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters",
        )
    if password.casefold() == username.casefold():
        raise HTTPException(status_code=400, detail="Password cannot match your username")
    if password.casefold() in COMMON_PASSWORDS:
        raise HTTPException(status_code=400, detail="Choose a less common password")


def enforce_login_throttle(
    connection: Any,
    username: str,
    request_client_key: str,
    now: float,
) -> None:
    """Raise 429 after five failures in the configured rolling window."""
    cutoff = now - LOGIN_WINDOW_SECONDS
    connection.execute("DELETE FROM login_failures WHERE failed_at < ?", (cutoff,))
    rows = connection.execute(
        """
        SELECT failed_at FROM login_failures
        WHERE username = ? AND client_key = ?
        ORDER BY failed_at ASC
        """,
        (username, request_client_key),
    ).fetchall()
    if len(rows) < LOGIN_MAX_FAILURES:
        return
    retry_after = max(
        1,
        math.ceil(LOGIN_WINDOW_SECONDS - (now - float(rows[0]["failed_at"]))),
    )
    raise HTTPException(
        status_code=429,
        detail="Too many login attempts. Try again later",
        headers={"Retry-After": str(retry_after)},
    )


def record_login_failure(
    connection: Any,
    username: str,
    request_client_key: str,
    now: float,
) -> None:
    """Record one failed credential check in the rolling throttle window."""
    connection.execute(
        "INSERT INTO login_failures (username, client_key, failed_at) VALUES (?, ?, ?)",
        (username, request_client_key, now),
    )
