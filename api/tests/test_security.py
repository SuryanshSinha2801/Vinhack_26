from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from api.app.core.config import settings
from api.app.database import SessionLocal
from api.app.main import app
from api.app.middleware import _rate_buckets
from api.app.models import SecurityAuditEvent
from api.app.routers.auth import _login_attempts
from api.app.schemas.checkins import CheckinSubmission
from pydantic import ValidationError
import pytest


def test_security_headers_are_added() -> None:
    response = TestClient(app).get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in response.headers["content-security-policy"]


def test_sensitive_responses_are_not_cached() -> None:
    response = TestClient(app).get("/v1/auth/me")
    assert response.headers["cache-control"] == "no-store, max-age=0"


def test_oversized_request_is_rejected() -> None:
    response = TestClient(app).post(
        "/v1/auth/login",
        content=b"x" * (settings.max_request_body_bytes + 1),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413


def test_nested_or_oversized_answers_are_rejected() -> None:
    with pytest.raises(ValidationError):
        CheckinSubmission(form_version="test", answers={"note": {"nested": "value"}})
    with pytest.raises(ValidationError):
        CheckinSubmission(form_version="test", answers={"note": "x" * 1_001})


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
        for _ in range(10):
            payload = {"username": f"missing-{uuid4().hex}", "password": "wrong-password"}
            assert client.post("/v1/auth/login", json=payload).status_code == 401
        payload = {"username": f"missing-{uuid4().hex}", "password": "wrong-password"}
        limited = client.post("/v1/auth/login", json=payload)
        assert limited.status_code == 429
        assert int(limited.headers["Retry-After"]) > 0
    finally:
        settings.rate_limit_enabled = previous
        _rate_buckets.clear()


def test_login_has_account_based_rate_limit() -> None:
    client = TestClient(app)
    username = f"target-{uuid4().hex}"
    _login_attempts.clear()
    try:
        for _ in range(6):
            assert client.post(
                "/v1/auth/login", json={"username": username, "password": "wrong-password"}
            ).status_code == 401
        assert client.post(
            "/v1/auth/login", json={"username": username, "password": "wrong-password"}
        ).status_code == 429
    finally:
        _login_attempts.clear()


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
