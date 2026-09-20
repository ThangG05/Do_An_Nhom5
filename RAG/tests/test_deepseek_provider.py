import json

import httpx
import pytest

from app.core.config import Settings
from app.llm.contracts import ContextBlock
from app.llm.providers.deepseek import DeepSeekProvider
from app.services.llm import LLMServiceError


def settings(**overrides) -> Settings:
    values = {
        "llm_provider": "deepseek",
        "llm_model": "deepseek-test",
        "llm_api_key": "test-key",
        "llm_base_url": "https://api.deepseek.test",
        "llm_timeout_seconds": 5,
        "llm_max_retries": 0,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.mark.asyncio
async def test_deepseek_provider_uses_shared_structured_contract() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert request.url.path == "/chat/completions"
        assert body["model"] == "deepseek-test"
        assert body["response_format"] == {"type": "json_object"}
        assert body["thinking"] == {"type": "disabled"}
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "answer": "Theo Điều 10... [1]",
            "refused": False,
            "refusal_reason": None,
            "cited_context_ids": ["chunk-1"],
        })}}]})

    client = httpx.AsyncClient(
        base_url="https://api.deepseek.test",
        transport=httpx.MockTransport(handler),
    )
    provider = DeepSeekProvider(settings(), client)
    result = await provider.answer(
        "Điều kiện tốt nghiệp là gì?",
        [ContextBlock(id="chunk-1", source_label="Quy chế", content="Điều 10: ...")],
    )
    assert result.cited_context_ids == ["chunk-1"]
    await client.aclose()


@pytest.mark.asyncio
async def test_deepseek_provider_rejects_invented_citation() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "answer": "Nội dung không có nguồn",
            "refused": False,
            "refusal_reason": None,
            "cited_context_ids": ["invented"],
        })}}]})

    client = httpx.AsyncClient(
        base_url="https://api.deepseek.test",
        transport=httpx.MockTransport(handler),
    )
    provider = DeepSeekProvider(settings(), client)
    with pytest.raises(LLMServiceError) as error:
        await provider.answer(
            "Câu hỏi hợp lệ?",
            [ContextBlock(id="chunk-1", source_label="Nguồn", content="Nội dung nguồn")],
        )
    assert error.value.code == "invalid_response"
    await client.aclose()


@pytest.mark.asyncio
async def test_deepseek_provider_maps_auth_error_without_leaking_body() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="provider secret error body")

    client = httpx.AsyncClient(
        base_url="https://api.deepseek.test",
        transport=httpx.MockTransport(handler),
    )
    provider = DeepSeekProvider(settings(), client)
    with pytest.raises(LLMServiceError) as error:
        await provider.answer(
            "Câu hỏi hợp lệ?",
            [ContextBlock(id="chunk-1", source_label="Nguồn", content="Nội dung nguồn")],
        )
    assert error.value.code == "invalid_api_key"
    assert "secret" not in str(error.value)
    await client.aclose()
