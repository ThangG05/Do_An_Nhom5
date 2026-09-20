"""Embedding provider adapters. Callers depend on the shared protocol, not vendors."""
import asyncio
import math
from typing import Protocol

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import get_settings


class EmbeddingError(RuntimeError):
    pass


class EmbeddingProvider(Protocol):
    async def embed_documents(self, texts: list[str], title: str) -> list[list[float]]: ...
    async def embed_query(self, text: str) -> list[float]: ...
    async def close(self) -> None: ...


def _validated_vectors(vectors: list[list[float]], expected_count: int, dimensions: int) -> list[list[float]]:
    if len(vectors) != expected_count: raise EmbeddingError("embedding provider returned an invalid vector count")
    normalized = []
    for values in vectors:
        if len(values) != dimensions: raise EmbeddingError("embedding dimensions do not match configuration")
        magnitude = math.sqrt(sum(value * value for value in values))
        if not magnitude: raise EmbeddingError("embedding provider returned a zero vector")
        normalized.append([value / magnitude for value in values])
    return normalized


class GeminiEmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.llm_api_key:
            raise EmbeddingError("LLM_API_KEY is not configured")
        self.client = genai.Client(api_key=self.settings.llm_api_key)

    async def embed_documents(self, texts: list[str], title: str) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.settings.embedding_batch_size):
            batch = texts[start:start + self.settings.embedding_batch_size]
            response = await self._request(batch, title)
            if not response.embeddings or len(response.embeddings) != len(batch):
                raise EmbeddingError("embedding provider returned an invalid response")
            for item in response.embeddings:
                values = list(item.values or [])
                if len(values) != self.settings.embedding_dimensions:
                    raise EmbeddingError("embedding dimensions do not match configuration")
                magnitude = math.sqrt(sum(value * value for value in values))
                if not magnitude:
                    raise EmbeddingError("embedding provider returned a zero vector")
                vectors.append([value / magnitude for value in values])
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        return (await self.embed_documents([text], "query"))[0]

    async def _request(self, texts: list[str], title: str):
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                async with asyncio.timeout(self.settings.llm_timeout_seconds):
                    return await self.client.aio.models.embed_content(
                        model=self.settings.embedding_model,
                        contents=texts,
                        config=types.EmbedContentConfig(
                            task_type="RETRIEVAL_DOCUMENT",
                            title=title[:500],
                            output_dimensionality=self.settings.embedding_dimensions,
                        ),
                    )
            except (TimeoutError, APIError) as exc:
                status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                transient = isinstance(exc, TimeoutError) or status in {429, 500, 502, 503, 504}
                if not transient or attempt == self.settings.llm_max_retries:
                    raise EmbeddingError("embedding provider unavailable") from exc
                await asyncio.sleep(self.settings.llm_retry_base_seconds * (2 ** attempt))
        raise EmbeddingError("embedding provider unavailable")

    async def close(self) -> None:
        await self.client.aio.aclose()


class ModalBgeM3EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        try:
            import modal
            self.remote = modal.Cls.from_name(
                self.settings.modal_embedding_app, self.settings.modal_embedding_class
            )()
        except Exception as exc:
            raise EmbeddingError("Modal embedding provider is not configured") from exc

    async def _embed(self, texts: list[str], input_type: str) -> list[list[float]]:
        if not texts or any(not text.strip() for text in texts): raise EmbeddingError("embedding input is empty")
        result = None
        for attempt in range(self.settings.embedding_max_retries + 1):
            try:
                async with asyncio.timeout(self.settings.embedding_timeout_seconds):
                    result = await asyncio.to_thread(self.remote.embed.remote, texts, input_type)
                break
            except Exception as exc:
                if attempt == self.settings.embedding_max_retries:
                    raise EmbeddingError("Modal embedding provider unavailable") from exc
                await asyncio.sleep(self.settings.embedding_retry_base_seconds * (2 ** attempt))
        if not isinstance(result, dict) or result.get("model") != self.settings.embedding_model:
            raise EmbeddingError("embedding provider returned unexpected model metadata")
        if result.get("dimensions") != self.settings.embedding_dimensions:
            raise EmbeddingError("embedding provider returned unexpected dimensions")
        return _validated_vectors(result.get("embeddings") or [], len(texts), self.settings.embedding_dimensions)

    async def embed_documents(self, texts: list[str], title: str) -> list[list[float]]:
        vectors = []
        for start in range(0, len(texts), self.settings.embedding_batch_size):
            vectors.extend(await self._embed(texts[start:start + self.settings.embedding_batch_size], "document"))
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        return (await self._embed([text], "query"))[0]

    async def close(self) -> None:
        return None


def get_embedding_provider() -> EmbeddingProvider:
    global _provider
    if _provider is not None:
        return _provider
    provider = get_settings().embedding_provider.casefold()
    if provider == "modal":
        _provider = ModalBgeM3EmbeddingService()
    elif provider == "gemini":
        _provider = GeminiEmbeddingService()
    else:
        raise EmbeddingError("unsupported embedding provider")
    return _provider


_provider: EmbeddingProvider | None = None


async def close_embedding_provider() -> None:
    global _provider
    if _provider is not None:
        await _provider.close()
        _provider = None
