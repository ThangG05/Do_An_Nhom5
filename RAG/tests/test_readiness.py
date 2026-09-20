from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes import health as health_routes
from app.main import app


def test_readiness_when_dependencies_are_available(monkeypatch) -> None:
    monkeypatch.setattr(health_routes, "check_database", AsyncMock(return_value=None))
    monkeypatch.setattr(health_routes, "check_qdrant", AsyncMock(return_value=None))
    monkeypatch.setattr(health_routes, "check_redis", AsyncMock(return_value=None))
    with TestClient(app) as client:
        response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ok", "qdrant": "ok", "redis": "ok"},
    }


def test_readiness_returns_503_without_leaking_error(monkeypatch) -> None:
    monkeypatch.setattr(health_routes, "check_database", AsyncMock(return_value=None))
    monkeypatch.setattr(health_routes, "check_qdrant", AsyncMock(side_effect=RuntimeError("secret")))
    monkeypatch.setattr(health_routes, "check_redis", AsyncMock(return_value=None))
    with TestClient(app) as client:
        response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["qdrant"] == "error"
    assert "secret" not in response.text
