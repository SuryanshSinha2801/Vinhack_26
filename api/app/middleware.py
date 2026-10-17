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
GLOBAL_RATE_LIMIT = (120, 60)
MAX_RATE_BUCKETS = 10_000
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
                path = scope.get("path", "")
                if path.startswith(("/v1/auth", "/v1/me", "/v1/checkins", "/v1/admin")):
                    headers["Cache-Control"] = "no-store, max-age=0"
                    headers["Pragma"] = "no-cache"
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


class RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") not in {"POST", "PUT", "PATCH", "DELETE"}:
            await self.app(scope, receive, send)
            return
        headers = MutableHeaders(scope=scope)
        content_length = headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > settings.max_request_body_bytes:
                    response = JSONResponse(status_code=413, content={"detail": "Request body is too large."})
                    await response(scope, receive, send)
                    return
            except ValueError:
                response = JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header."})
                await response(scope, receive, send)
                return

        buffered: list[Message] = []
        total = 0
        more_body = True
        while more_body:
            message = await receive()
            buffered.append(message)
            if message["type"] == "http.disconnect":
                break
            if message["type"] == "http.request":
                total += len(message.get("body", b""))
                more_body = message.get("more_body", False)
                if total > settings.max_request_body_bytes:
                    response = JSONResponse(status_code=413, content={"detail": "Request body is too large."})
                    await response(scope, receive, send)
                    return

        async def replay() -> Message:
            if buffered:
                return buffered.pop(0)
            return {"type": "http.request", "body": b"", "more_body": False}

        await self.app(scope, replay, send)


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        rule = RATE_LIMITS.get((request.method, request.url.path))
        if not settings.rate_limit_enabled:
            await self.app(scope, receive, send)
            return
        identity = request.client.host if request.client else "unknown"
        now = monotonic()
        with _rate_lock:
            rules = [(GLOBAL_RATE_LIMIT, (identity, "*", "*"))]
            if rule:
                rules.append((rule, (identity, request.method, request.url.path)))
            for (limit, window), key in rules:
                bucket = _rate_buckets.get(key)
                if bucket is None:
                    if len(_rate_buckets) >= MAX_RATE_BUCKETS:
                        stale = [stored_key for stored_key, values in _rate_buckets.items() if not values or values[-1] <= now - 3600]
                        for stored_key in stale[:1000]:
                            _rate_buckets.pop(stored_key, None)
                    if len(_rate_buckets) >= MAX_RATE_BUCKETS:
                        response = JSONResponse(status_code=429, content={"detail": "Traffic limit reached."})
                        await response(scope, receive, send)
                        return
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
            for (_limit, _window), key in rules:
                _rate_buckets[key].append(now)
        await self.app(scope, receive, send)
