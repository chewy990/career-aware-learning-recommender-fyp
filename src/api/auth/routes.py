"""Define the unchanged `/api/auth` HTTP contract.

Routes orchestrate focused security and storage services. They must not contain
schema migrations or cryptographic implementations.
"""

from __future__ import annotations

import secrets
import time

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response

from api.auth.dependencies import require_user
from api.auth.security import hash_password, normalise_username, token_digest
from api.auth.sessions import (
    clear_session_cookie,
    establish_session,
)
from api.auth.storage import auth_connection, is_unique_violation
from api.auth.validation import (
    enforce_login_throttle,
    record_login_failure,
    validate_new_password,
    validate_registration_username,
    validate_request_origin,
)
from api.config import (
    AUTH_COOKIE_NAME,
    DUMMY_SALT,
)
from api.rate_limit import client_key, enforce_auth_rate_limit
from api.schemas import AuthRequest, ChangePasswordRequest

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register")
def register(
    payload: AuthRequest,
    request: Request,
    response: Response,
) -> dict[str, object]:
    """Create an account and establish its first session."""
    validate_request_origin(request)
    enforce_auth_rate_limit(request, "register")
    username = normalise_username(payload.username)
    validate_registration_username(username)
    validate_new_password(username, payload.password)
    salt = secrets.token_hex(16)
    password_hash = hash_password(payload.password, salt)
    try:
        with auth_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (username, password_hash, salt)
                VALUES (?, ?, ?)
                """,
                (username, password_hash, salt),
            )
    except Exception as exc:
        if is_unique_violation(exc):
            raise HTTPException(
                status_code=409,
                detail="Username already exists",
            ) from exc
        raise
    return establish_session(username, response)


@router.post("/login")
def login(
    payload: AuthRequest,
    request: Request,
    response: Response,
) -> dict[str, object]:
    """Verify current credentials and establish a session."""
    validate_request_origin(request)
    enforce_auth_rate_limit(request, "login")
    username = normalise_username(payload.username)
    request_client_key = client_key(request)
    now = time.time()
    with auth_connection() as connection:
        enforce_login_throttle(connection, username, request_client_key, now)
        row = connection.execute(
            """
            SELECT username, password_hash, salt
            FROM users WHERE username = ?
            """,
            (username,),
        ).fetchone()
        if row:
            password_hash = hash_password(payload.password, str(row["salt"]))
            password_matches = secrets.compare_digest(
                password_hash,
                str(row["password_hash"]),
            )
        else:
            # Constant-work dummy hashing reduces username-enumeration timing.
            password_hash = hash_password(payload.password, DUMMY_SALT)
            password_matches = secrets.compare_digest(password_hash, "0" * 64)

        if not password_matches or not row:
            record_login_failure(connection, username, request_client_key, now)
            authenticated_username = ""
        else:
            authenticated_username = str(row["username"])
            connection.execute(
                "DELETE FROM login_failures WHERE username = ? AND client_key = ?",
                (username, request_client_key),
            )
    if not authenticated_username:
        raise HTTPException(status_code=401, detail="Username or password is incorrect")
    return establish_session(authenticated_username, response)


@router.get("/me")
def auth_me(
    response: Response,
    username: str = Depends(require_user),
) -> dict[str, object]:
    """Return the current username without allowing response caching."""
    response.headers["Cache-Control"] = "no-store"
    return {"username": username}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    username: str = Depends(require_user),
) -> dict[str, object]:
    """Verify and replace a password, revoking all prior sessions."""
    validate_request_origin(request)
    validate_new_password(username, payload.new_password)
    if secrets.compare_digest(payload.current_password, payload.new_password):
        raise HTTPException(status_code=400, detail="New password must be different")

    with auth_connection() as connection:
        row = connection.execute(
            """
            SELECT password_hash, salt
            FROM users WHERE username = ?
            """,
            (username,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Session expired")
        current_hash = hash_password(
            payload.current_password,
            str(row["salt"]),
        )
        if not secrets.compare_digest(current_hash, str(row["password_hash"])):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        next_salt = secrets.token_hex(16)
        next_hash = hash_password(payload.new_password, next_salt)
        connection.execute(
            """
            UPDATE users SET password_hash = ?, salt = ?
            WHERE username = ?
            """,
            (next_hash, next_salt, username),
        )
        connection.execute("DELETE FROM sessions WHERE username = ?", (username,))
        connection.execute("DELETE FROM login_failures WHERE username = ?", (username,))
    return establish_session(username, response)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    session_token: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
) -> dict[str, str]:
    """Revoke the current session and clear its browser cookie."""
    validate_request_origin(request)
    if session_token:
        with auth_connection() as connection:
            connection.execute(
                "DELETE FROM sessions WHERE token_hash = ?",
                (token_digest(session_token),),
            )
    clear_session_cookie(response)
    return {"status": "ok"}
