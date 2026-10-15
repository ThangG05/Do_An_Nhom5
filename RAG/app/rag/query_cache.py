"""Small in-process cache for query vectors, with concurrent requests sharing one embed call.

Only a hash of each query and its vector are retained. Document embeddings are not cached.
"""
import asyncio
from collections import OrderedDict
from hashlib import sha256
from time import monotonic
from typing import Awaitable, Callable


class QueryEmbeddingCache:
    def __init__(self, max_entries: int, ttl_seconds: float) -> None:
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._values: OrderedDict[str, tuple[float, tuple[float, ...]]] = OrderedDict()
        self._inflight: dict[str, asyncio.Task[list[float]]] = {}

    async def get_or_embed(self, model: str, query: str,
                           embed: Callable[[], Awaitable[list[float]]]) -> list[float]:
        if self.max_entries == 0 or self.ttl_seconds == 0:
            return await embed()
        key = sha256(f"{model}\0{query}".encode("utf-8")).hexdigest()
        now = monotonic()
        cached = self._values.get(key)
        if cached is not None:
            expires_at, vector = cached
            if expires_at > now:
                self._values.move_to_end(key)
                return list(vector)
            del self._values[key]

        task = self._inflight.get(key)
        if task is None:
            task = asyncio.create_task(embed())
            self._inflight[key] = task

            def finish(completed: asyncio.Task[list[float]]) -> None:
                if self._inflight.get(key) is completed:
                    del self._inflight[key]
                try:
                    vector = completed.result()
                except (Exception, asyncio.CancelledError):
                    return  # Do not cache failed or cancelled provider calls.
                self._values[key] = (monotonic() + self.ttl_seconds, tuple(vector))
                self._values.move_to_end(key)
                while len(self._values) > self.max_entries:
                    self._values.popitem(last=False)

            task.add_done_callback(finish)
        # One HTTP request being cancelled must not cancel an embed shared by other requests.
        return list(await asyncio.shield(task))
