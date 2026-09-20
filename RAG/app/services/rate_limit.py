import hashlib
import time
from uuid import uuid4
from app.core.config import get_settings
from app.services.redis import get_redis_client


class RateLimitExceeded(RuntimeError):
    pass


class ConcurrencyLimitExceeded(RuntimeError):
    pass


async def enforce_rag_rate_limit(identifier: str) -> None:
    settings = get_settings()
    digest = hashlib.sha256(identifier.encode()).hexdigest()
    key = f"hvnh:rate:rag:{digest}"
    script = "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n"
    count = int(await get_redis_client().eval(script, 1, key))
    if count > settings.rag_rate_limit_per_minute:
        raise RateLimitExceeded("rate limit exceeded")


async def acquire_rag_slot() -> str:
    settings = get_settings(); token = str(uuid4()); now = time.time()
    # A lease must survive every configured provider attempt and exponential backoff.
    retry_backoff = settings.llm_retry_base_seconds * (2 ** settings.llm_max_retries - 1)
    minimum_lease = int(settings.llm_timeout_seconds * (settings.llm_max_retries + 1)
                        + retry_backoff + 15)
    lease_seconds = max(settings.rag_concurrency_lease_seconds, minimum_lease)
    key = "hvnh:concurrency:rag"
    script = """redis.call('ZREMRANGEBYSCORE',KEYS[1],'-inf',ARGV[1]);
    if redis.call('ZCARD',KEYS[1]) >= tonumber(ARGV[2]) then return 0 end;
    redis.call('ZADD',KEYS[1],ARGV[3],ARGV[4]); redis.call('EXPIRE',KEYS[1],ARGV[5]); return 1"""
    acquired = int(await get_redis_client().eval(script, 1, key, now,
        settings.rag_global_concurrency, now + lease_seconds,
        token, lease_seconds))
    if not acquired: raise ConcurrencyLimitExceeded("global concurrency limit reached")
    return token


async def release_rag_slot(token: str) -> None:
    await get_redis_client().zrem("hvnh:concurrency:rag", token)
