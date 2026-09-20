from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes import internal_llm
from app.core.config import Settings
from app.llm.contracts import LLMAnswer
from app.main import app


def test_internal_llm_endpoint_requires_key(monkeypatch) -> None:
    monkeypatch.setattr(internal_llm, "get_settings", lambda: Settings(
        _env_file=None, internal_api_key="internal-test-key"
    ))
    response = TestClient(app).post("/api/v1/internal/llm/test")
    assert response.status_code == 401


def test_internal_llm_endpoint_uses_selected_provider(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
        internal_api_key="internal-test-key",
        llm_provider="deepseek",
        llm_model="deepseek-test",
    )
    provider = type("Provider", (), {})()
    provider.answer = AsyncMock(return_value=LLMAnswer(
        answer="HVNH Hub [1]", cited_context_ids=["internal-health-check"]
    ))
    monkeypatch.setattr(internal_llm, "get_settings", lambda: settings)
    monkeypatch.setattr(internal_llm, "get_llm_provider", lambda: provider)
    response = TestClient(app).post(
        "/api/v1/internal/llm/test",
        headers={"X-Internal-API-Key": "internal-test-key"},
    )
    assert response.status_code == 200
    assert response.json()["provider"] == "deepseek"
    assert response.json()["cited_context_ids"] == ["internal-health-check"]
