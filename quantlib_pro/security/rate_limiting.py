"""
Tiered rate limiting for API and computation endpoints.

Three tiers:
    BASIC    — free / default users   (60 req/min, 5 heavy/min)
    PREMIUM  — paying users           (300 req/min, 30 heavy/min)
    INTERNAL — internal services      (no limit)

Two sliding-window implementations:
    InMemoryRateLimiter  — process-local (dev / single-instance)
    RedisRateLimiter     — distributed   (production)

Usage::

    limiter = InMemoryRateLimiter()

    @rate_limit("compute:options", tier=Tier.BASIC)
    def price_option(..., *, auth_ctx):
        ...
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Any, Callable, Optional, TypeVar

log = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class Tier(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    INTERNAL = "internal"


class RateLimitError(RuntimeError):
    def __init__(self, endpoint: str, tier: Tier, retry_after: float) -> None:
        self.endpoint = endpoint
        self.tier = tier
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for '{endpoint}' (tier={tier.value}). "
            f"Retry after {retry_after:.1f}s."
        )


@dataclass
class RateLimit:
    """Requests allowed within *window_seconds*."""
    max_requests: int
    window_seconds: int


# Tier × endpoint_type → RateLimit
_LIMITS: dict[Tier, dict[str, RateLimit]] = {
    Tier.BASIC: {
        "default": RateLimit(60, 60),
        "heavy":   RateLimit(5, 60),
        "export":  RateLimit(10, 3600),
    },
    Tier.PREMIUM: {
        "default": RateLimit(300, 60),
        "heavy":   RateLimit(30, 60),
        "export":  RateLimit(100, 3600),
    },
    Tier.INTERNAL: {
        "default": RateLimit(10_000, 60),
        "heavy":   RateLimit(10_000, 60),
        "export":  RateLimit(10_000, 3600),
    },
}


# ─── In-memory limiter ────────────────────────────────────────────────────────

class InMemoryRateLimiter:
    """
    Sliding-window rate limiter backed by a per-(user, endpoint_type)
    deque of timestamps.  Thread-safe via a single reentrant lock.
    """

    def __init__(self) -> None:
        # {(user_id, endpoint_type): deque of timestamps}
        self._windows: dict[tuple[str, str], deque] = {}
        self._lock = Lock()

    def check(
        self,
        user_id: str,
        endpoint_type: str,
        tier: Tier,
    ) -> None:
        """
        Raise :class:`RateLimitError` if the user has exceeded their quota.

        Parameters
        ----------
        user_id:
            Unique identifier for the caller.
        endpoint_type:
            One of ``"default"``, ``"heavy"``, ``"export"``.
        tier:
            The caller's service tier.
        """
        limit = _LIMITS[tier].get(endpoint_type, _LIMITS[tier]["default"])
        now = time.monotonic()
        window_start = now - limit.window_seconds

        key = (user_id, endpoint_type)
        with self._lock:
            if key not in self._windows:
                self._windows[key] = deque()
            dq = self._windows[key]

            # Remove expired entries
            while dq and dq[0] < window_start:
                dq.popleft()

            if len(dq) >= limit.max_requests:
                oldest = dq[0]
                retry_after = oldest + limit.window_seconds - now
                raise RateLimitError(endpoint_type, tier, max(0.0, retry_after))

            dq.append(now)


# ─── Redis limiter ────────────────────────────────────────────────────────────

class RedisRateLimiter:
    """
    Sliding-window rate limiter backed by Redis sorted-sets.

    Uses atomic MULTI/EXEC to prevent race conditions in distributed
    deployments.

    Parameters
    ----------
    redis_client:
        A ``redis.Redis`` instance.
    key_prefix:
        Namespace prefix to avoid collisions in shared Redis.
    """

    def __init__(self, redis_client: Any, key_prefix: str = "qlp:rl") -> None:
        self._redis = redis_client
        self._prefix = key_prefix

    def check(
        self,
        user_id: str,
        endpoint_type: str,
        tier: Tier,
    ) -> None:
        limit = _LIMITS[tier].get(endpoint_type, _LIMITS[tier]["default"])
        now = time.time()
        window_start = now - limit.window_seconds
        redis_key = f"{self._prefix}:{user_id}:{endpoint_type}"

        try:
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(redis_key, 0, window_start)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {f"{now}": now})
            pipe.expire(redis_key, limit.window_seconds + 1)
            results = pipe.execute()
            count_before_add = results[1]
        except Exception as exc:
            log.warning("Redis rate limiter error — passing request through: %s", exc)
            return   # fail open: don't block on Redis outage

        if count_before_add >= limit.max_requests:
            # Undo the zadd we already executed
            try:
                self._redis.zrem(redis_key, f"{now}")
            except Exception:
                pass
            oldest_score = self._redis.zrange(redis_key, 0, 0, withscores=True)
            if oldest_score:
                retry_after = oldest_score[0][1] + limit.window_seconds - now
            else:
                retry_after = 1.0
            raise RateLimitError(endpoint_type, tier, max(0.0, retry_after))


# ─── Default singleton ────────────────────────────────────────────────────────

_default_limiter = InMemoryRateLimiter()


def get_default_limiter() -> InMemoryRateLimiter:
    return _default_limiter


# ─── Decorator ────────────────────────────────────────────────────────────────

def rate_limit(
    endpoint_type: str = "default",
    tier: Tier = Tier.BASIC,
    limiter: Optional[InMemoryRateLimiter] = None,
) -> Callable[[F], F]:
    """
    Decorator that enforces rate limiting based on the ``auth_ctx.user_id``.

    Requires the decorated function to accept an ``auth_ctx`` keyword
    argument (compatible with authentication.AuthContext).
    """
    _limiter = limiter or _default_limiter

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = kwargs.get("auth_ctx")
            user_id = ctx.user_id if ctx else "anonymous"
            _tier = Tier(ctx.extra.get("tier", tier.value)) if ctx else tier
            _limiter.check(user_id, endpoint_type, _tier)
            return fn(*args, **kwargs)
        return wrapper  # type: ignore[return-value]
    return decorator
