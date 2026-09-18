from fastapi.testclient import TestClient

from api.app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "status": "ok",
            "service": "MindTrail API",
            "environment": "development",
        },
        "error": None,
    }


def test_versioned_health_endpoint() -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200

