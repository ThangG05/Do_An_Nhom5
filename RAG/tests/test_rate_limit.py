from unittest.mock import AsyncMock
import pytest
from app.core.config import Settings
from app.services import rate_limit


@pytest.mark.asyncio
async def test_rate_limiter_rejects_above_limit(monkeypatch) -> None:
    redis = SimpleRedis = type("SimpleRedis", (), {})()
    redis.eval = AsyncMock(return_value=11)
    monkeypatch.setattr(rate_limit, "get_settings", lambda: Settings(_env_file=None, rag_rate_limit_per_minute=10))
    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: redis)
    with pytest.raises(rate_limit.RateLimitExceeded):
        await rate_limit.enforce_rag_rate_limit("user:private-id")
    key = redis.eval.await_args.args[2]
    assert "private-id" not in key


@pytest.mark.asyncio
async def test_global_concurrency_fails_closed(monkeypatch) -> None:
    redis = type("SimpleRedis", (), {})(); redis.eval = AsyncMock(return_value=0)
    monkeypatch.setattr(rate_limit, "get_settings", lambda: Settings(_env_file=None))
    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: redis)
    with pytest.raises(rate_limit.ConcurrencyLimitExceeded):
        await rate_limit.acquire_rag_slot()


@pytest.mark.asyncio
async def test_concurrency_lease_covers_all_llm_retries(monkeypatch) -> None:
    redis = type("SimpleRedis", (), {})(); redis.eval = AsyncMock(return_value=1)
    settings = Settings(_env_file=None, llm_timeout_seconds=60, llm_max_retries=2,
                        llm_retry_base_seconds=1, rag_concurrency_lease_seconds=30)
    monkeypatch.setattr(rate_limit, "get_settings", lambda: settings)
    monkeypatch.setattr(rate_limit, "get_redis_client", lambda: redis)
    await rate_limit.acquire_rag_slot()
    assert int(redis.eval.await_args.args[-1]) >= 198
