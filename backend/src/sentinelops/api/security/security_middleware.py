"""
Security Middleware — System 12
Malformed payload rejection, rate-limit headers, offline-safe.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityMiddleware(BaseHTTPMiddleware):
    """Lightweight request-level protection. No auth, no cloud."""

    # Simple in-memory rate limiter per IP (fallback if Redis unavailable)
    _ip_hits: dict[str, list[float]] = defaultdict(list)
    RATE_LIMIT = 300   # requests
    RATE_WINDOW = 60   # seconds

    def __init__(self, app: ASGIApp, max_body_bytes: int = 512_000) -> None:
        super().__init__(app)
        self._max_body = max_body_bytes

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()

        # Sliding-window rate limit
        hits = self._ip_hits[ip]
        self._ip_hits[ip] = [t for t in hits if now - t < self.RATE_WINDOW]
        if len(self._ip_hits[ip]) >= self.RATE_LIMIT:
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )
        self._ip_hits[ip].append(now)

        # Content-length guard
        cl = request.headers.get("content-length")
        if cl and int(cl) > self._max_body:
            return Response(
                content='{"detail":"Payload too large"}',
                status_code=413,
                media_type="application/json",
            )

        response = await call_next(request)
        response.headers["X-SentinelOps-Version"] = "1.0"
        response.headers["X-Frame-Options"] = "DENY"
        return response
