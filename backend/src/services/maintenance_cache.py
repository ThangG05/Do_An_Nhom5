"""Short-lived, per-worker snapshot for the public maintenance gate."""

import asyncio
import time
from collections.abc import Callable

from starlette.concurrency import run_in_threadpool

from src.db.session import SessionLocal
from src.models.system import MaintenanceResponse
from src.services.system_service import maintenance


def _load_maintenance() -> MaintenanceResponse:
    with SessionLocal() as db:
        return maintenance(db)


class MaintenanceCache:
    def __init__(self, loader: Callable[[], MaintenanceResponse] = _load_maintenance, ttl_seconds: float = 2.0):
        self._loader = loader
        self._ttl_seconds = ttl_seconds
        self._lock = asyncio.Lock()
        self._state: MaintenanceResponse | None = None
        self._expires_at = 0.0
        self._generation = 0

    async def get(self) -> MaintenanceResponse:
        if self._state is not None and time.monotonic() < self._expires_at:
            return self._state
        async with self._lock:
            if self._state is not None and time.monotonic() < self._expires_at:
                return self._state
            while True:
                generation = self._generation
                state = await run_in_threadpool(self._loader)
                if generation == self._generation:
                    self._state = state
                    self._expires_at = time.monotonic() + self._ttl_seconds
                    return state

    def invalidate(self) -> None:
        self._generation += 1
        self._state = None
        self._expires_at = 0.0
