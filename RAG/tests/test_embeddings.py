from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.rag.embeddings import EmbeddingError, GeminiEmbeddingService, _validated_vectors


def test_shared_embedding_validation_normalizes_vectors() -> None:
    assert _validated_vectors([[3.0, 4.0]], 1, 2) == [[0.6, 0.8]]
    with pytest.raises(EmbeddingError, match="zero vector"):
        _validated_vectors([[0.0, 0.0]], 1, 2)


@pytest.mark.asyncio
async def test_embedding_service_validates_and_normalizes_vectors() -> None:
    service = GeminiEmbeddingService.__new__(GeminiEmbeddingService)
    service.settings = SimpleNamespace(embedding_batch_size=20, embedding_dimensions=3)
    service._request = AsyncMock(return_value=SimpleNamespace(
        embeddings=[SimpleNamespace(values=[3.0, 4.0, 0.0])]
    ))
    vectors = await service.embed_documents(["quy chế"], "Quy chế")
    assert vectors == [[0.6, 0.8, 0.0]]


@pytest.mark.asyncio
async def test_embedding_service_rejects_wrong_dimensions() -> None:
    service = GeminiEmbeddingService.__new__(GeminiEmbeddingService)
    service.settings = SimpleNamespace(embedding_batch_size=20, embedding_dimensions=3)
    service._request = AsyncMock(return_value=SimpleNamespace(
        embeddings=[SimpleNamespace(values=[1.0, 2.0])]
    ))
    with pytest.raises(EmbeddingError, match="dimensions"):
        await service.embed_documents(["thông báo"], "Thông báo")
