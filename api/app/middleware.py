from collections import defaultdict, deque
from secrets import compare_digest
from threading import Lock
from time import monotonic

from fastapi import Request
from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api.app.core.config import settings
from api.app.routers.auth import COOKIE_NAME, CSRF_COOKIE_NAME


RATE_LIMITS = {
    ("POST", "/v1/auth/login"): (10, 300),
    ("POST", "/v1/auth/register"): (5, 3600),
    ("POST", "/v1/checkins"): (10, 60),
    ("GET", "/v1/me/export"): (5, 60),
    ("DELETE", "/v1/me/data"): (5, 3600),
}
_rate_buckets: dict[tuple[str, str, str], deque[float]] = defaultdict(deque)
_rate_lock = Lock()


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
                headers["Content-Security-Policy"] = (
                    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' "
                    "https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; "
                    "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
                    "base-uri 'self'; form-action 'self'"
                )
                if settings.app_env == "production":
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            await send(message)

        await self.app(scope, receive, send_with_headers)


class CSRFMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        if (
            settings.csrf_enabled
            and request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and request.cookies.get(COOKIE_NAME)
        ):
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
            header_token = request.headers.get("X-CSRF-Token", "")
            if not cookie_token or not header_token or not compare_digest(cookie_token, header_token):
                response = JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        rule = RATE_LIMITS.get((request.method, request.url.path))
        if not settings.rate_limit_enabled or not rule:
            await self.app(scope, receive, send)
            return
        limit, window = rule
        identity = request.client.host if request.client else "unknown"
        key = (identity, request.method, request.url.path)
        now = monotonic()
        with _rate_lock:
            bucket = _rate_buckets[key]
            while bucket and bucket[0] <= now - window:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = max(1, int(window - (now - bucket[0])))
                response = JSONResponse(
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                    content={"detail": "Too many requests. Please try again later."},
                )
                await response(scope, receive, send)
                return
            bucket.append(now)
        await self.app(scope, receive, send)
