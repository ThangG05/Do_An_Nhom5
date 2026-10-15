import asyncio

import pytest

from app.rag.query_cache import QueryEmbeddingCache


@pytest.mark.asyncio
async def test_repeated_query_reuses_vector_without_retaining_plaintext() -> None:
    cache = QueryEmbeddingCache(max_entries=2, ttl_seconds=60)
    calls = 0

    async def embed() -> list[float]:
        nonlocal calls
        calls += 1
        return [0.1, 0.2]

    first = await cache.get_or_embed("bge-m3", "Học phí là gì?", embed)
    first[0] = 99  # Callers cannot mutate cached vectors.
    assert await cache.get_or_embed("bge-m3", "Học phí là gì?", embed) == [0.1, 0.2]
    assert calls == 1
    assert "Học phí" not in repr(cache._values)


@pytest.mark.asyncio
async def test_concurrent_equal_queries_share_one_embedding_call() -> None:
    cache = QueryEmbeddingCache(max_entries=2, ttl_seconds=60)
    calls = 0

    async def embed() -> list[float]:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return [0.3]

    vectors = await asyncio.gather(*(cache.get_or_embed("bge-m3", "VSTEP", embed) for _ in range(5)))
    assert vectors == [[0.3]] * 5
    assert calls == 1


@pytest.mark.asyncio
async def test_cancelled_waiter_does_not_cancel_shared_embedding() -> None:
    cache = QueryEmbeddingCache(max_entries=2, ttl_seconds=60)
    started = asyncio.Event()
    finish = asyncio.Event()
    calls = 0

    async def embed() -> list[float]:
        nonlocal calls
        calls += 1
        started.set()
        await finish.wait()
        return [0.8]

    first = asyncio.create_task(cache.get_or_embed("bge-m3", "VSTEP", embed))
    await started.wait()
    second = asyncio.create_task(cache.get_or_embed("bge-m3", "VSTEP", embed))
    await asyncio.sleep(0)
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    finish.set()
    assert await second == [0.8]
    assert calls == 1


@pytest.mark.asyncio
async def test_failed_embedding_is_not_cached() -> None:
    cache = QueryEmbeddingCache(max_entries=2, ttl_seconds=60)
    calls = 0

    async def embed() -> list[float]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("unavailable")
        return [0.4]

    with pytest.raises(RuntimeError):
        await cache.get_or_embed("bge-m3", "VSTEP", embed)
    assert await cache.get_or_embed("bge-m3", "VSTEP", embed) == [0.4]
    assert calls == 2


@pytest.mark.asyncio
async def test_model_changes_do_not_reuse_vectors() -> None:
    cache = QueryEmbeddingCache(max_entries=2, ttl_seconds=60)
    calls = 0

    async def embed() -> list[float]:
        nonlocal calls
        calls += 1
        return [float(calls)]

    assert await cache.get_or_embed("model-a", "VSTEP", embed) == [1.0]
    assert await cache.get_or_embed("model-b", "VSTEP", embed) == [2.0]


@pytest.mark.asyncio
async def test_expired_vectors_are_recomputed(monkeypatch) -> None:
    clock = [100.0]
    monkeypatch.setattr("app.rag.query_cache.monotonic", lambda: clock[0])
    cache = QueryEmbeddingCache(max_entries=2, ttl_seconds=10)
    calls = 0

    async def embed() -> list[float]:
        nonlocal calls
        calls += 1
        return [float(calls)]

    assert await cache.get_or_embed("bge-m3", "VSTEP", embed) == [1.0]
    clock[0] = 111.0
    assert await cache.get_or_embed("bge-m3", "VSTEP", embed) == [2.0]
