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
    """FastAPI middleware for rate limiting."""

    def __init__(
        self,
        app,
        rate: int = 60,
        per_seconds: int = 60,
        exclude_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.limiter = RateLimiter(rate=rate, per_seconds=per_seconds)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/health",
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip excluded paths
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return await call_next(request)

        # Use client IP or auth token as key
        client_ip = request.client.host if request.client else "unknown"
        auth_header = request.headers.get("Authorization", "")
        key = auth_header if auth_header else client_ip

        if not self.limiter.is_allowed(key):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
            )

        response = await call_next(request)
        return response
