from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
AUTH_DB_PATH = DATA_DIR / "auth.sqlite3"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
IS_PRODUCTION = APP_ENV == "production"

TOP_K = 12
EVALUATION_K = 5
MODELS = ("popularity", "content_based", "hybrid")

PBKDF2_ITERATIONS = 600_000
PASSWORD_MIN_LENGTH = 12
AUTH_COOKIE_NAME = "id"
SESSION_IDLE_SECONDS = 2 * 60 * 60
SESSION_ABSOLUTE_SECONDS = 12 * 60 * 60
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_FAILURES = 5
MAX_REQUEST_BODY_BYTES = 128 * 1024
AUTH_GLOBAL_RATE_LIMIT = (20, 60)
LOGIN_IP_RATE_LIMIT = (10, 60)
REGISTER_IP_RATE_LIMIT = (5, 5 * 60)
COMPUTE_GLOBAL_RATE_LIMIT = (60, 60)
COMPUTE_IP_RATE_LIMIT = (30, 60)
USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,39}$")

DEFAULT_ALLOWED_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
ALLOWED_ORIGINS = tuple(
    origin.strip()
    for origin in os.getenv("AUTH_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",")
    if origin.strip()
)
AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "").strip().lower() in {
    "1",
    "true",
    "yes",
}
AUTH_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "strict").strip().lower()
AUTH_REQUIRE_ORIGIN = os.getenv(
    "AUTH_REQUIRE_ORIGIN",
    "true" if IS_PRODUCTION else "false",
).strip().lower() in {"1", "true", "yes"}
if AUTH_COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    raise RuntimeError("AUTH_COOKIE_SAMESITE must be lax, strict, or none")
if AUTH_COOKIE_SAMESITE == "none" and not AUTH_COOKIE_SECURE:
    raise RuntimeError("SameSite=None cookies require AUTH_COOKIE_SECURE=true")

COMMON_PASSWORDS = {
    "111111111111",
    "123456789012",
    "123456789123",
    "1234qwerasdf",
    "1q2w3e4r5t6y",
    "1qaz2wsx3edc",
    "987654321098",
    "abcdef123456",
    "adminadmin123",
    "baseball1234",
    "basketball12",
    "changeme1234",
    "computer1234",
    "dragon123456",
    "football1234",
    "iloveyou1234",
    "letmein123456",
    "loginlogin1234",
    "monkey123456",
    "password1234",
    "password12345",
    "password123456",
    "princess1234",
    "qwerty123456",
    "qwertyuiop12",
    "sunshine1234",
    "trustnoone123",
    "welcome12345",
    "whatever1234",
    "zaq12wsxcde3",
}
DUMMY_SALT = "0" * 32
