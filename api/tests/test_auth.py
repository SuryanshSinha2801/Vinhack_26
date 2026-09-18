from uuid import uuid4

from fastapi.testclient import TestClient

from api.app.main import app


def test_register_session_logout_and_login() -> None:
    client = TestClient(app)
    username = f"student-{uuid4().hex}"
    credentials = {"username": username, "display_name": "Asha", "password": "correct-horse"}

    registered = client.post("/v1/auth/register", json=credentials)
    assert registered.status_code == 201
    assert registered.json()["data"]["display_name"] == "Asha"
    assert registered.cookies.get("mindtrail_session")
    assert client.get("/v1/auth/me").status_code == 200

    assert client.post("/v1/auth/logout").status_code == 204
    assert client.get("/v1/auth/me").status_code == 401

    logged_in = client.post(
        "/v1/auth/login", json={"username": username, "password": "correct-horse"}
    )
    assert logged_in.status_code == 200
    assert client.get("/v1/auth/me").json()["data"]["username"] == username


def test_login_rejects_bad_password() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/auth/login",
        json={"username": f"missing-{uuid4().hex}", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_excel_seeded_demo_user_can_login() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/auth/login",
        json={"username": "arjun01", "password": "Trail@Arjun26"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["display_name"] == "Arjun"
