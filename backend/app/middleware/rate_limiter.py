"""
Rate limiting middleware for auth endpoints.
In-memory sliding window — no extra dependencies.
"""
import time
import logging
from collections import defaultdict
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Rate limit config: path_prefix → (max_requests, window_seconds)
RATE_LIMITS = {
    "/api/auth/login": (5, 60),           # 5 attempts per minute
    "/api/auth/register": (3, 60),        # 3 per minute
    "/api/auth/forgot-password": (3, 300), # 3 per 5 minutes
    "/api/auth/reset-password": (5, 300),  # 5 per 5 minutes
    "/api/analyses/upload": (10, 600),     # 10 uploads per 10 minutes
}


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self, app):
        super().__init__(app)
        # {(client_ip, path): [timestamp, ...]}
        self._requests: dict[tuple, list] = defaultdict(list)
        self._last_cleanup = time.time()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        await super().__call__(scope, receive, send)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Only rate-limit POST requests to auth endpoints
        if method != "POST":
            return await call_next(request)

        limit_config = None
        for prefix, config in RATE_LIMITS.items():
            if path == prefix or path.rstrip("/") == prefix:
                limit_config = config
                break

        if not limit_config:
            return await call_next(request)

        max_requests, window_seconds = limit_config
        client_ip = self._get_client_ip(request)
        key = (client_ip, path)
        now = time.time()

        # Cleanup old entries periodically (every 60s)
        if now - self._last_cleanup > 60:
            self._cleanup(now)
            self._last_cleanup = now

        # Remove expired timestamps for this key
        self._requests[key] = [
            ts for ts in self._requests[key]
            if now - ts < window_seconds
        ]

        if len(self._requests[key]) >= max_requests:
            retry_after = int(window_seconds - (now - self._requests[key][0]))
            logger.warning(
                f"Rate limit exceeded: {client_ip} on {path} "
                f"({len(self._requests[key])}/{max_requests} in {window_seconds}s)"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": max(retry_after, 1),
                },
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        self._requests[key].append(now)
        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"

    def _cleanup(self, now: float):
        """Remove all expired entries to prevent memory leak."""
        max_window = max(w for _, w in RATE_LIMITS.values())
        expired_keys = [
            key for key, timestamps in self._requests.items()
            if not timestamps or now - timestamps[-1] > max_window
        ]
        for key in expired_keys:
            del self._requests[key]
