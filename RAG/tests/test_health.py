from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "HVNH RAG AI Service"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"]


def test_request_id_is_preserved_only_when_safe() -> None:
    with TestClient(app) as client:
        accepted = client.get("/api/v1/health", headers={"X-Request-ID": "web-123"})
        replaced = client.get("/api/v1/health", headers={"X-Request-ID": "bad id\nvalue"})
    assert accepted.headers["x-request-id"] == "web-123"
    assert replaced.headers["x-request-id"] != "bad id\nvalue"


def test_oversized_request_is_rejected_before_authentication() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/rag/chat", content=b"x" * 70000,
                               headers={"Content-Type": "application/json"})
    assert response.status_code == 413
    assert response.json() == {"detail": "Request body too large"}
