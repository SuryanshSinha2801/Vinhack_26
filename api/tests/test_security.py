from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from api.app.core.config import settings
from api.app.database import SessionLocal
from api.app.main import app
from api.app.middleware import _rate_buckets
from api.app.models import SecurityAuditEvent


def test_security_headers_are_added() -> None:
    response = TestClient(app).get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in response.headers["content-security-policy"]


def test_cookie_session_requires_csrf_for_mutation() -> None:
    client = TestClient(app)
    previous = settings.csrf_enabled
    settings.csrf_enabled = True
    try:
        response = client.post(
            "/v1/auth/register",
            json={
                "username": f"csrf-{uuid4().hex}",
                "display_name": "CSRF Test",
                "password": "correct-horse",
            },
        )
        assert response.status_code == 201
        token = client.cookies.get("mindtrail_csrf")
        assert token
        assert client.post("/v1/auth/logout").status_code == 403
        assert client.post("/v1/auth/logout", headers={"X-CSRF-Token": token}).status_code == 204
    finally:
        settings.csrf_enabled = previous


def test_login_rate_limit() -> None:
    client = TestClient(app)
    previous = settings.rate_limit_enabled
    settings.rate_limit_enabled = True
    _rate_buckets.clear()
    try:
        payload = {"username": f"missing-{uuid4().hex}", "password": "wrong-password"}
        for _ in range(10):
            assert client.post("/v1/auth/login", json=payload).status_code == 401
        limited = client.post("/v1/auth/login", json=payload)
        assert limited.status_code == 429
        assert int(limited.headers["Retry-After"]) > 0
    finally:
        settings.rate_limit_enabled = previous
        _rate_buckets.clear()


def test_login_audit_does_not_store_username() -> None:
    username = f"audit-{uuid4().hex}"
    TestClient(app).post("/v1/auth/login", json={"username": username, "password": "wrong-password"})
    with SessionLocal() as db:
        event = db.scalar(
            select(SecurityAuditEvent)
            .where(SecurityAuditEvent.event_type == "auth.login")
            .order_by(SecurityAuditEvent.id.desc())
        )
        assert event is not None
        assert len(event.actor_reference) == 64
        assert username not in str(event.event_data)
