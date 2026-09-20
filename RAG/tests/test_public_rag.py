from fastapi.testclient import TestClient
from app.api.dependencies import auth
from app.core.config import Settings
from app.main import app


def test_public_rag_is_disabled_without_jwt_secret(monkeypatch) -> None:
    monkeypatch.setattr(auth, "get_settings", lambda: Settings(_env_file=None, auth_jwt_secret=None))
    response = TestClient(app).post("/api/v1/rag/chat", json={"question": "VSTEP là gì?"})
    assert response.status_code == 503
