from uuid import uuid4

from fastapi.testclient import TestClient

from api.app.core.security import hash_password
from api.app.database import SessionLocal
from api.app.main import app
from api.app.models import User


def test_admin_dashboard_requires_authentication_and_role() -> None:
    anonymous = TestClient(app)
    assert anonymous.get("/v1/admin/dashboard").status_code == 401

    student = TestClient(app)
    assert student.post(
        "/v1/auth/login", json={"username": "arjun01", "password": "Trail@Arjun26"}
    ).status_code == 200
    assert student.get("/v1/admin/dashboard").status_code == 403


def test_admin_dashboard_is_aggregate_only() -> None:
    username = f"admin-{uuid4().hex}"
    password = "secure-admin-password"
    with SessionLocal() as db:
        db.add(
            User(
                username=username,
                display_name="Test Administrator",
                password_hash=hash_password(password),
                role="admin",
            )
        )
        db.commit()

    client = TestClient(app)
    login = client.post("/v1/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    assert login.json()["data"]["role"] == "admin"

    response = client.get("/v1/admin/dashboard?days=180")
    assert response.status_code == 200
    dashboard = response.json()["data"]
    assert dashboard["privacy_minimum_group"] == 5
    assert dashboard["active_students"] >= 40
    assert dashboard["checkins_in_window"] > 0
    assert dashboard["daily"]
    def all_keys(value):
        if isinstance(value, dict):
            return set(value).union(*(all_keys(item) for item in value.values()))
        if isinstance(value, list):
            return set().union(*(all_keys(item) for item in value), set())
        return set()

    keys = all_keys(dashboard)
    assert "username" not in keys
    assert "answers" not in keys
    for day in dashboard["daily"]:
        if day["suppressed"]:
            assert day["average_mood"] is None
            assert day["average_stress"] is None
            assert day["follow_up_requests"] is None
