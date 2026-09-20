from fastapi.testclient import TestClient
from app.api.routes import internal_rag
from app.core.config import Settings
from app.main import app


def test_internal_rag_endpoint_requires_key(monkeypatch) -> None:
    monkeypatch.setattr(internal_rag, "get_settings", lambda: Settings(
        _env_file=None, internal_api_key="internal-test-key"
    ))
    response = TestClient(app).post("/api/v1/internal/rag/ask", json={"question": "VSTEP là gì?"})
    assert response.status_code == 401


def test_internal_rag_request_validation_runs_before_service(monkeypatch) -> None:
    monkeypatch.setattr(internal_rag, "get_settings", lambda: Settings(
        _env_file=None, internal_api_key="internal-test-key"
    ))
    response = TestClient(app).post("/api/v1/internal/rag/ask",
        headers={"X-Internal-API-Key": "internal-test-key"}, json={"question": ""})
    assert response.status_code == 422
