from redis.asyncio import Redis
import certifi

from app.core.config import get_settings

_client: Redis | None = None


def get_redis_client() -> Redis:
    global _client
    if _client is None:
        settings = get_settings()
        connection_kwargs = {}
        if settings.redis_connection_uri.startswith("rediss://"):
            connection_kwargs["ssl_ca_certs"] = certifi.where()
            connection_kwargs["ssl_cert_reqs"] = "required"
        _client = Redis.from_url(
            settings.redis_connection_uri,
            socket_connect_timeout=settings.redis_timeout_seconds,
            # Blocking stream reads must have headroom beyond XREADGROUP BLOCK.
            socket_timeout=max(
                settings.redis_timeout_seconds,
                settings.crawler_queue_block_ms / 1000 + 5,
            ),
            health_check_interval=30,
            decode_responses=True,
            **connection_kwargs,
        )
    return _client


async def check_redis() -> None:
    if not await get_redis_client().ping():
        raise ConnectionError("Redis ping returned a false response")


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
