import asyncio
import json
import logging
import secrets
import time
import uuid
from collections import defaultdict
from contextlib import suppress
from typing import Any, Iterable

from fastapi import WebSocket

from src.config import settings

try:
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover - optional in local-only mode
    Redis = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Local WebSocket connections backed by an optional Redis event bus."""

    def __init__(self) -> None:
        self.connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self.instance_id = uuid.uuid4().hex
        self._redis: Any | None = None
        self._listener_task: asyncio.Task[None] | None = None
        self._presence_task: asyncio.Task[None] | None = None
        self._tickets: dict[str, tuple[uuid.UUID, float]] = {}
        self._channel = f"{settings.REALTIME_REDIS_PREFIX}:events"

    @property
    def redis_enabled(self) -> bool:
        return self._redis is not None

    async def start(self) -> None:
        redis_url = settings.REALTIME_REDIS_URL or settings.REDIS_URL
        if not redis_url or Redis is None:
            logger.warning("Realtime Redis is disabled; delivery is limited to this backend instance.")
            return
        try:
            self._redis = Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=settings.REALTIME_REDIS_CONNECT_TIMEOUT_SECONDS,
                socket_timeout=settings.REALTIME_REDIS_SOCKET_TIMEOUT_SECONDS,
                health_check_interval=30,
            )
            await self._redis.ping()
            self._listener_task = asyncio.create_task(self._listen(), name="realtime-redis-listener")
            self._presence_task = asyncio.create_task(self._refresh_presence(), name="realtime-presence")
            logger.info("Realtime Redis Pub/Sub enabled for instance %s", self.instance_id)
        except Exception:
            logger.exception("Cannot connect to realtime Redis; using local-only delivery.")
            if self._redis is not None:
                with suppress(Exception):
                    await self._redis.aclose()
            self._redis = None

    async def stop(self) -> None:
        for task in (self._listener_task, self._presence_task):
            if task is not None:
                task.cancel()
        for task in (self._listener_task, self._presence_task):
            if task is not None:
                with suppress(asyncio.CancelledError):
                    await task
        self._listener_task = self._presence_task = None
        if self._redis is not None:
            for user_id in list(self.connections):
                with suppress(Exception):
                    await self._redis.delete(self._presence_key(user_id))
            with suppress(Exception):
                await self._redis.aclose()
        self._redis = None

    async def issue_ticket(self, user_id: uuid.UUID) -> str:
        ticket = secrets.token_urlsafe(32)
        ttl = settings.WEBSOCKET_TICKET_EXPIRE_SECONDS
        if self._redis is not None:
            try:
                await self._redis.set(self._ticket_key(ticket), str(user_id), ex=ttl, nx=True)
                return ticket
            except Exception:
                logger.exception("Could not store WebSocket ticket in Redis; using local ticket storage.")
        now = time.monotonic()
        self._tickets = {key: value for key, value in self._tickets.items() if value[1] > now}
        self._tickets[ticket] = (user_id, now + ttl)
        return ticket

    async def consume_ticket(self, ticket: str) -> uuid.UUID | None:
        if not ticket:
            return None
        if self._redis is not None:
            try:
                value = await self._redis.getdel(self._ticket_key(ticket))
                if value:
                    try:
                        return uuid.UUID(value)
                    except ValueError:
                        return None
            except Exception:
                logger.exception("Could not consume WebSocket ticket from Redis.")
        value = self._tickets.pop(ticket, None)
        if value is None or value[1] <= time.monotonic():
            return None
        return value[0]

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[user_id].add(websocket)
        await self._mark_online(user_id)

    async def disconnect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        sockets = self.connections.get(user_id)
        if sockets is not None:
            sockets.discard(websocket)
            if not sockets:
                self.connections.pop(user_id, None)
                if self._redis is not None:
                    with suppress(Exception):
                        await self._redis.delete(self._presence_key(user_id))

    async def is_online(self, user_id: uuid.UUID) -> bool:
        if self.connections.get(user_id):
            return True
        if self._redis is None:
            return False
        async for _ in self._redis.scan_iter(match=f"{settings.REALTIME_REDIS_PREFIX}:presence:{user_id}:*", count=10):
            return True
        return False

    def is_online_local(self, user_id: uuid.UUID) -> bool:
        """Return a synchronous local hint for DB services."""
        return bool(self.connections.get(user_id))

    async def send_users(self, user_ids: Iterable[uuid.UUID], payload: dict[str, Any]) -> None:
        unique_ids = list(dict.fromkeys(str(user_id) for user_id in user_ids))
        if not unique_ids:
            return
        if self._redis is not None:
            try:
                await self._redis.publish(self._channel, json.dumps({"user_ids": unique_ids, "payload": payload}, default=str))
                return
            except Exception:
                logger.exception("Redis publish failed; falling back to local delivery.")
        await self._send_local((uuid.UUID(value) for value in unique_ids), payload)

    async def _send_local(self, user_ids: Iterable[uuid.UUID], payload: dict[str, Any]) -> None:
        stale: list[tuple[uuid.UUID, WebSocket]] = []
        for user_id in user_ids:
            for websocket in list(self.connections.get(user_id, set())):
                try:
                    await websocket.send_json(payload)
                except Exception:
                    stale.append((user_id, websocket))
        for user_id, websocket in stale:
            await self.disconnect(user_id, websocket)

    async def _listen(self) -> None:
        assert self._redis is not None
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self._channel)
        try:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                try:
                    event = json.loads(message["data"])
                    await self._send_local([uuid.UUID(value) for value in event["user_ids"]], event["payload"])
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    logger.warning("Ignored malformed realtime Redis event.")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Realtime Redis listener stopped unexpectedly.")
        finally:
            with suppress(Exception):
                await pubsub.unsubscribe(self._channel)
                await pubsub.aclose()

    async def _refresh_presence(self) -> None:
        while True:
            try:
                for user_id in list(self.connections):
                    await self._mark_online(user_id)
                await asyncio.sleep(settings.REALTIME_PRESENCE_REFRESH_SECONDS)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Could not refresh realtime presence.")
                await asyncio.sleep(settings.REALTIME_PRESENCE_REFRESH_SECONDS)

    async def _mark_online(self, user_id: uuid.UUID) -> None:
        if self._redis is not None:
            try:
                await self._redis.set(self._presence_key(user_id), "1", ex=settings.REALTIME_PRESENCE_TTL_SECONDS)
            except Exception:
                logger.exception("Could not update realtime presence for user %s.", user_id)

    def _presence_key(self, user_id: uuid.UUID) -> str:
        return f"{settings.REALTIME_REDIS_PREFIX}:presence:{user_id}:{self.instance_id}"

    def _ticket_key(self, ticket: str) -> str:
        return f"{settings.REALTIME_REDIS_PREFIX}:ticket:{ticket}"


manager = ConnectionManager()
