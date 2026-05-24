"""Rate limiting middleware using token bucket algorithm."""

import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimiter:
    """Simple in-memory token bucket rate limiter."""

    def __init__(self, rate: int = 60, per_seconds: int = 60) -> None:
        self.rate = rate
        self.per_seconds = per_seconds
        self._buckets: dict[str, tuple[float, int]] = defaultdict(
            lambda: (time.time(), rate)
        )

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for the given key."""
        now = time.time()
        last_refill, tokens = self._buckets[key]

        # Refill tokens
        elapsed = now - last_refill
        refill = int(elapsed * (self.rate / self.per_seconds))
        tokens = min(self.rate, tokens + refill)

        if tokens > 0:
            self._buckets[key] = (now, tokens - 1)
            return True
        else:
            self._buckets[key] = (
                now if refill > 0 else last_refill,
                tokens,
            )
            return False

    def cleanup(self) -> None:
        """Remove stale buckets."""
        now = time.time()
        stale = [
            key
            for key, (last_refill, tokens) in self._buckets.items()
            if now - last_refill > self.per_seconds * 2 and tokens == self.rate
        ]
        for key in stale:
            del self._buckets[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting with per-path limits."""

    def __init__(
        self,
        app,
        rate: int = 60,
        per_seconds: int = 60,
        path_limits: dict[str, tuple[int, int]] | None = None,
        exclude_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.default_limiter = RateLimiter(rate=rate, per_seconds=per_seconds)
        self.path_limits: dict[str, RateLimiter] = {}
        if path_limits:
            for path, (r, s) in path_limits.items():
                self.path_limits[path] = RateLimiter(rate=r, per_seconds=s)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/health",
        ]

    def _get_client_key(self, request: Request) -> str:
        """Derive a rate-limit key: client IP for unauthenticated, user+IP for auth."""
        client_ip = request.client.host if request.client else "unknown"
        auth_header = request.headers.get("Authorization", "")
        if auth_header:
            return f"{client_ip}:token"
        return client_ip

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip excluded paths
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return await call_next(request)

        key = self._get_client_key(request)

        # Check per-path limits first (stricter), then default
        limiter = self.default_limiter
        for path_prefix, path_limiter in self.path_limits.items():
            if request.url.path.startswith(path_prefix):
                limiter = path_limiter
                break

        if not limiter.is_allowed(key):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
            )

        response = await call_next(request)
        return response
