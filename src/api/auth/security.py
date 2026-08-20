"""Provide password hashing and opaque token digests.

Only cryptographic transformations belong here; policy and persistence are
kept elsewhere so security decisions remain auditable.
"""

from __future__ import annotations

import hashlib

from api.config import PBKDF2_ITERATIONS


def normalise_username(username: str) -> str:
    """Return the canonical account identifier used by storage and throttling."""
    return username.strip().lower()


def hash_password(
    password: str,
    salt: str,
) -> str:
    """Derive a password hash using the current fixed PBKDF2 policy."""
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    )
    return digest.hex()


def token_digest(token: str) -> str:
    """Hash a session token so raw bearer credentials never enter SQLite."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
