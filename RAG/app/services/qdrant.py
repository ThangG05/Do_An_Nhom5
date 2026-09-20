import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from qdrant_client import AsyncQdrantClient

from app.core.config import get_settings

_client: AsyncQdrantClient | None = None
T = TypeVar("T")


async def qdrant_retry(operation: Callable[[], Awaitable[T]]) -> T:
    """Retry idempotent Qdrant operations without logging request payloads."""
    settings = get_settings()
    for attempt in range(settings.qdrant_max_retries + 1):
        try:
            return await operation()
        except Exception:
            if attempt == settings.qdrant_max_retries:
                raise
            await asyncio.sleep(settings.qdrant_retry_base_seconds * (2 ** attempt))
    raise AssertionError("unreachable")


def get_qdrant_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncQdrantClient(
            url=settings.qdrant_connection_url,
            api_key=settings.qdrant_api_key or None,
            timeout=settings.qdrant_timeout_seconds,
            check_compatibility=False,
        )
    return _client


async def check_qdrant() -> None:
    await get_qdrant_client().get_collections()


async def close_qdrant() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
