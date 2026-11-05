"""Fail-open Redis cache for validated, evidence-grounded answer payloads."""
import asyncio
from hashlib import sha256
import json
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.llm.contracts import ContextBlock, LLMAnswer

logger = logging.getLogger(__name__)
_CACHE_SCHEMA = "v1"


def answer_cache_key(question: str, blocks: list[ContextBlock], model: str,
                     prompt_fingerprint: str) -> str:
    """Tie an answer to the exact ordered evidence and generation contract."""
    evidence = [{
        "content": sha256(block.content.encode("utf-8")).hexdigest(),
        "source": block.source_label,
        "source_key": block.source_key,
    } for block in blocks]
    payload = json.dumps({
        "schema": _CACHE_SCHEMA,
        "question": question,
        "evidence": evidence,
        "model": model,
        "prompt": prompt_fingerprint,
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "hvnh:rag:grounded-answer:v1:" + sha256(payload.encode("utf-8")).hexdigest()


class GroundedAnswerCache:
    def __init__(self, client: Redis, ttl_seconds: int, timeout_seconds: float) -> None:
        self.client = client
        self.ttl_seconds = ttl_seconds
        self.timeout_seconds = timeout_seconds

    async def get(self, key: str) -> LLMAnswer | None:
        if self.ttl_seconds <= 0:
            return None
        try:
            raw = await asyncio.wait_for(self.client.get(key), self.timeout_seconds)
            if raw is None:
                return None
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            answer = LLMAnswer.model_validate_json(raw)
            if answer.refused:
                return None
            return answer
        except (RedisError, TimeoutError, ValueError, TypeError, UnicodeDecodeError):
            logger.debug("rag_answer_cache_read_failed", exc_info=True)
            return None

    async def set(self, key: str, answer: LLMAnswer) -> None:
        if self.ttl_seconds <= 0 or answer.refused:
            return
        try:
            await asyncio.wait_for(
                self.client.set(key, answer.model_dump_json(), ex=self.ttl_seconds),
                self.timeout_seconds,
            )
        except (RedisError, TimeoutError, ValueError, TypeError):
            # Cache is an optimization only; never turn a healthy answer into an error.
            logger.debug("rag_answer_cache_write_failed", exc_info=True)
