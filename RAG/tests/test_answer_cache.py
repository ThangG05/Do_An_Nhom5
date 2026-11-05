from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.llm.contracts import ContextBlock, LLMAnswer
from app.rag.answer_cache import GroundedAnswerCache, answer_cache_key


def _blocks(content: str = "Evidence") -> list[ContextBlock]:
    return [ContextBlock(id="1", content=content, source_label="Policy 2026", source_key="doc-v2")]


def test_answer_cache_key_tracks_question_evidence_model_and_prompt() -> None:
    base = answer_cache_key("What is the rule?", _blocks(), "gemini:model-a", "prompt-v1")
    assert base != answer_cache_key("What is the rule?", _blocks("Updated evidence"), "gemini:model-a", "prompt-v1")
    assert base != answer_cache_key("What is the rule?", _blocks(), "deepseek:model-a", "prompt-v1")
    assert base != answer_cache_key("What is the rule?", _blocks(), "gemini:model-a", "prompt-v2")
    assert base != answer_cache_key("Different question", _blocks(), "gemini:model-a", "prompt-v1")


@pytest.mark.asyncio
async def test_answer_cache_round_trips_only_grounded_answers() -> None:
    client = SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock())
    cache = GroundedAnswerCache(client, ttl_seconds=60, timeout_seconds=0.2)
    answer = LLMAnswer(answer="The rule is X [1].", cited_context_ids=["1"])
    await cache.set("key", answer)
    client.get.return_value = answer.model_dump_json()
    assert await cache.get("key") == answer

    await cache.set("refused", LLMAnswer(
        answer="No matching source.", refused=True, refusal_reason="insufficient_context",
        cited_context_ids=[]))
    client.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_answer_cache_fails_open_on_redis_errors() -> None:
    client = SimpleNamespace(get=AsyncMock(side_effect=TimeoutError()), set=AsyncMock(side_effect=TimeoutError()))
    cache = GroundedAnswerCache(client, ttl_seconds=60, timeout_seconds=0.01)
    answer = LLMAnswer(answer="The rule is X [1].", cited_context_ids=["1"])
    assert await cache.get("key") is None
    await cache.set("key", answer)  # A cache outage must not bubble into answer generation.
