"""In-memory token-bucket rate limiter for auth endpoints.

Deliberately dependency-free (no Redis required) so the API runs with zero
external services in dev. The bucket map is process-local: behind multiple
workers you would swap :class:`TokenBucketLimiter` for a Redis-backed one, but
the *interface* (``allow(key) -> bool``) stays identical so call sites do not
change. Keyed by client IP + route so one abusive caller cannot lock out others.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from app.core.config import settings


@dataclass
class _Bucket:
    tokens: float
    updated_at: float = field(default_factory=time.monotonic)


class TokenBucketLimiter:
    """Thread-safe token bucket: ``capacity`` burst, ``refill`` tokens/second."""

    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self.capacity = max(1, capacity)
        self.refill_per_sec = max(0.0, refill_per_sec)
        self._buckets: dict[str, _Bucket] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """Consume one token for ``key``; return False when the bucket is empty."""
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = _Bucket(tokens=float(self.capacity), updated_at=now)
                self._buckets[key] = bucket
            elapsed = now - bucket.updated_at
            bucket.tokens = min(
                float(self.capacity), bucket.tokens + elapsed * self.refill_per_sec
            )
            bucket.updated_at = now
            if bucket.tokens < 1.0:
                return False
            bucket.tokens -= 1.0
            return True

    def reset(self) -> None:
        """Drop all buckets (used by tests)."""
        with self._lock:
            self._buckets.clear()


#: One shared limiter for the auth surface (login/register/refresh).
auth_limiter = TokenBucketLimiter(
    capacity=settings.RATE_LIMIT_AUTH_CAPACITY,
    refill_per_sec=settings.RATE_LIMIT_AUTH_REFILL_PER_SEC,
)
