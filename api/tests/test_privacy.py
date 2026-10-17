from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from api.app.database import SessionLocal
from api.app.main import app
from api.app.models import ConsentRecord, User


def registered_client() -> tuple[TestClient, str, str]:
    client = TestClient(app)
    username = f"privacy-{uuid4().hex}"
    password = "private-test-password"
    response = client.post(
        "/v1/auth/register",
        json={"username": username, "display_name": "Privacy Test", "password": password},
    )
    assert response.status_code == 201
    return client, username, password


def test_consent_history_controls_personalization() -> None:
    client, username, _password = registered_client()
    initial = client.get("/v1/me/consent")
    assert initial.status_code == 200
    assert initial.json()["data"]["personalization_enabled"] is True

    updated = client.post("/v1/me/consent", json={"personalization_enabled": False})
    assert updated.status_code == 200
    assert updated.json()["data"]["personalization_enabled"] is False
    checkin = client.get("/v1/checkins/today").json()["data"]
    assert checkin["personalization"]["personalized"] is False
    assert "were not used" in checkin["personalization"]["explanation"]

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        records = db.scalars(
            select(ConsentRecord).where(ConsentRecord.user_id == user.id)
        ).all()
        assert len(records) == 1


def test_export_contains_only_authenticated_users_data() -> None:
    assert TestClient(app).get("/v1/me/export").status_code == 401
    client, username, _password = registered_client()
    response = client.get("/v1/me/export")
    assert response.status_code == 200
    exported = response.json()["data"]
    assert exported["username"] == username
    assert exported["checkins"] == []
    assert exported["consent_history"] == []
    assert "password" not in str(exported).lower()


def test_delete_requires_password_and_removes_own_account() -> None:
    client, username, password = registered_client()
    client.post("/v1/me/consent", json={"personalization_enabled": False})

    invalid = client.request(
        "DELETE",
        "/v1/me/data",
        json={"password": "incorrect-password", "confirmation": "DELETE"},
    )
    assert invalid.status_code == 401

    deleted = client.request(
        "DELETE",
        "/v1/me/data",
        json={"password": password, "confirmation": "DELETE"},
    )
    assert deleted.status_code == 204
    assert client.get("/v1/auth/me").status_code == 401

    with SessionLocal() as db:
        assert db.scalar(select(User).where(User.username == username)) is None
