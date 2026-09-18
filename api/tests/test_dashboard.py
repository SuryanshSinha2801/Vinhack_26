from fastapi.testclient import TestClient

from api.app.main import app


def test_demo_dashboard_requires_authentication() -> None:
    assert TestClient(app).get("/v1/me/dashboard").status_code == 401


def test_demo_dashboard_returns_only_logged_in_users_history() -> None:
    client = TestClient(app)
    login = client.post(
        "/v1/auth/login",
        json={"username": "arjun01", "password": "Trail@Arjun26"},
    )
    assert login.status_code == 200

    response = client.get("/v1/me/dashboard")
    assert response.status_code == 200
    dashboard = response.json()["data"]
    assert dashboard["username"] == "arjun01"
    assert dashboard["summary"]["days"] == 15
    assert len(dashboard["history"]) == 15
    assert all(item["date"] >= "2026-09-05" for item in dashboard["history"])
