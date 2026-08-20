"""Small in-process rate limits for the single-instance public prototype."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from threading import Lock

from fastapi import HTTPException, Request

from api.config import (
    AUTH_GLOBAL_RATE_LIMIT,
    COMPUTE_GLOBAL_RATE_LIMIT,
    COMPUTE_IP_RATE_LIMIT,
    LOGIN_IP_RATE_LIMIT,
    REGISTER_IP_RATE_LIMIT,
)


@dataclass
class _Bucket:
    tokens: float
    updated_at: float


class _TokenBucketLimiter:
    """Apply bounded token buckets without adding a network dependency."""

    def __init__(self) -> None:
        self._buckets: dict[tuple[str, str], _Bucket] = {}
        self._lock = Lock()

    def enforce(
        self,
        scope: str,
        key: str,
        capacity: int,
        window_seconds: int,
    ) -> None:
        now = time.monotonic()
        refill_rate = capacity / window_seconds
        bucket_key = (scope, key)
        with self._lock:
            bucket = self._buckets.get(bucket_key, _Bucket(float(capacity), now))
            elapsed = max(0.0, now - bucket.updated_at)
            bucket.tokens = min(float(capacity), bucket.tokens + elapsed * refill_rate)
            bucket.updated_at = now
            self._buckets[bucket_key] = bucket
            if bucket.tokens >= 1:
                bucket.tokens -= 1
                self._prune(now)
                return
            retry_after = max(1, math.ceil((1 - bucket.tokens) / refill_rate))
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Try again shortly",
            headers={"Retry-After": str(retry_after)},
        )

    def _prune(self, now: float) -> None:
        if len(self._buckets) <= 4096:
            return
        stale_before = now - 3600
        self._buckets = {
            key: bucket
            for key, bucket in self._buckets.items()
            if bucket.updated_at >= stale_before
        }

    def clear(self) -> None:
        """Clear process-local buckets for deterministic tests."""
        with self._lock:
            self._buckets.clear()


_LIMITER = _TokenBucketLimiter()


def client_key(request: Request) -> str:
    """Return the client address resolved by the trusted hosting proxy."""
    return request.client.host if request.client else "unknown"


def enforce_auth_rate_limit(request: Request, action: str) -> None:
    """Protect public password hashing from cheap request floods."""
    global_capacity, global_window = AUTH_GLOBAL_RATE_LIMIT
    _LIMITER.enforce("auth-global", "all", global_capacity, global_window)
    capacity, window = (
        REGISTER_IP_RATE_LIMIT if action == "register" else LOGIN_IP_RATE_LIMIT
    )
    _LIMITER.enforce(f"auth-{action}", client_key(request), capacity, window)


def enforce_compute_rate_limit(request: Request) -> None:
    """Bound repeated recommendation work globally and per client."""
    global_capacity, global_window = COMPUTE_GLOBAL_RATE_LIMIT
    _LIMITER.enforce("compute-global", "all", global_capacity, global_window)
    capacity, window = COMPUTE_IP_RATE_LIMIT
    _LIMITER.enforce("compute-client", client_key(request), capacity, window)


def reset_rate_limits() -> None:
    """Reset process-local state between tests."""
    _LIMITER.clear()
