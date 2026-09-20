from dataclasses import dataclass
from uuid import UUID, uuid4

from redis.asyncio import Redis

from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class QueueMessage:
    message_id: str
    run_id: UUID


class CrawlQueue:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.settings = get_settings()

    async def ensure_group(self) -> None:
        try:
            await self.redis.xgroup_create(self.settings.crawler_stream,
                                           self.settings.crawler_consumer_group, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def enqueue(self, run_id: UUID) -> str:
        return await self.redis.xadd(self.settings.crawler_stream, {"run_id": str(run_id)})

    async def consume(self) -> QueueMessage | None:
        await self.ensure_group()
        rows = await self.redis.xreadgroup(
            self.settings.crawler_consumer_group, self.settings.crawler_consumer_name,
            {self.settings.crawler_stream: ">"}, count=1,
            block=self.settings.crawler_queue_block_ms,
        )
        if not rows:
            return None
        _, entries = rows[0]
        message_id, values = entries[0]
        return QueueMessage(message_id, UUID(values["run_id"]))

    async def acknowledge(self, message_id: str) -> None:
        await self.redis.xack(self.settings.crawler_stream,
                              self.settings.crawler_consumer_group, message_id)

    async def acquire_source_lock(self, source_id: UUID) -> str | None:
        token = str(uuid4())
        acquired = await self.redis.set(f"hvnh:crawl:lock:{source_id}", token,
                                        nx=True, ex=self.settings.crawler_lock_seconds)
        return token if acquired else None

    async def release_source_lock(self, source_id: UUID, token: str) -> None:
        script = "if redis.call('get',KEYS[1])==ARGV[1] then return redis.call('del',KEYS[1]) else return 0 end"
        await self.redis.eval(script, 1, f"hvnh:crawl:lock:{source_id}", token)
