from __future__ import annotations

import logging
import os
import time
from typing import Callable, Optional, Tuple

from fastapi import HTTPException, Request

logger = logging.getLogger("balancevault.ratelimit")

# In-memory fallback bucket store: { key: [timestamps] }
_MEMORY_STORE: dict[str, list[float]] = {}
_REDIS_CLIENT = None
_REDIS_INITIALIZED = False


def get_redis_client():
    global _REDIS_CLIENT, _REDIS_INITIALIZED
    if _REDIS_INITIALIZED:
        return _REDIS_CLIENT

    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            import redis
            _REDIS_CLIENT = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            _REDIS_CLIENT.ping()
            logger.info("Connected to Redis at %s", redis_url.split("@")[-1])
        except Exception as exc:
            logger.warning("Could not connect to Redis (%s). Using in-memory fallback rate limiter.", exc)
            _REDIS_CLIENT = None
    else:
        _REDIS_CLIENT = None

    _REDIS_INITIALIZED = True
    return _REDIS_CLIENT


def check_redis_health() -> Tuple[bool, str]:
    """Check Redis health for readiness probe."""
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        return True, "not_configured (in-memory rate limiter active)"

    client = get_redis_client()
    if client is None:
        return False, "unreachable"

    try:
        client.ping()
        return True, "healthy"
    except Exception as exc:
        return False, f"unreachable: {str(exc)}"


def check_rate_limit(key: str, limit: int, window_seconds: int = 60) -> Tuple[bool, int]:
    """
    Check if a key has exceeded the allowed rate limit.
    Returns (allowed: bool, retry_after: int).
    """
    enabled = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
    if not enabled:
        return True, 0

    client = get_redis_client()
    fail_safe = os.environ.get("RATE_LIMIT_FAIL_SAFE", "true").lower() in ("true", "1", "yes")

    if client is not None:
        try:
            redis_key = f"ratelimit:{key}"
            pipe = client.pipeline()
            pipe.incr(redis_key)
            pipe.ttl(redis_key)
            results = pipe.execute()
            current = results[0]
            ttl = results[1]

            if current == 1 or ttl == -1:
                client.expire(redis_key, window_seconds)
                ttl = window_seconds

            if current > limit:
                return False, max(1, ttl)
            return True, 0
        except Exception as exc:
            logger.warning("Redis rate limit check failed: %s", exc)
            if not fail_safe:
                return False, window_seconds

    # Fallback to in-memory sliding window
    now = time.time()
    cutoff = now - window_seconds
    timestamps = _MEMORY_STORE.setdefault(key, [])
    # Prune old timestamps
    _MEMORY_STORE[key] = [t for t in timestamps if t > cutoff]

    if len(_MEMORY_STORE[key]) >= limit:
        oldest = _MEMORY_STORE[key][0]
        retry_after = max(1, int(window_seconds - (now - oldest)))
        return False, retry_after

    _MEMORY_STORE[key].append(now)
    return True, 0


def reset_memory_store():
    """Reset the in-memory store (for testing)."""
    global _MEMORY_STORE
    _MEMORY_STORE.clear()


def rate_limit(limit: int, window_seconds: int = 60, key_prefix: str = "general") -> Callable:
    """FastAPI dependency to enforce rate limits per client IP or actor."""
    def dependency(request: Request):
        # Extract IP or token subject
        client_ip = "unknown"
        if request.client:
            client_ip = request.client.host

        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        rate_key = f"{key_prefix}:{client_ip}"
        allowed, retry_after = check_rate_limit(rate_key, limit=limit, window_seconds=window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {limit} requests per {window_seconds}s.",
                headers={"Retry-After": str(retry_after)},
            )
        return True

    return dependency
