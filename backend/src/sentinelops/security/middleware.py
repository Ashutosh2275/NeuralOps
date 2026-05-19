"""FastAPI middleware for security hardening"""

from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

from sentinelops.security.hardening import (
    rate_limiter,
    RequestValidator,
    security_audit_log,
    get_client_id,
)

log = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API rate limiting"""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)

        client_id = get_client_id(request)

        if not rate_limiter.is_allowed(client_id):
            retry_after = rate_limiter.get_retry_after(client_id)
            security_audit_log.log_rate_limit_exceeded(
                client_id,
                str(request.url.path)
            )

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )

        response = await call_next(request)
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate incoming requests"""

    MAX_CONTENT_LENGTH = 10_000_000  # 10MB

    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.MAX_CONTENT_LENGTH:
                    client_id = get_client_id(request)
                    security_audit_log.log_invalid_request(
                        client_id,
                        f"Payload exceeds max size: {content_length}"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Payload too large"}
                    )
            except ValueError:
                pass

        # Check headers for suspicious patterns
        user_agent = request.headers.get("user-agent", "")
        if len(user_agent) > 500:
            client_id = get_client_id(request)
            security_audit_log.log_invalid_request(
                client_id,
                "Suspiciously long user-agent header"
            )

        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


def setup_security_middleware(app: FastAPI):
    """Register all security middleware with FastAPI app"""

    # Order matters: add in this order
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestValidationMiddleware)
    app.add_middleware(RateLimitMiddleware)

    log.info("Security middleware configured")
