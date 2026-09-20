"""Load and run the completed RAG application inside the backend process."""

from __future__ import annotations

import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAG_ROOT = PROJECT_ROOT / "RAG"

if not (RAG_ROOT / "app" / "main.py").is_file():
    raise RuntimeError(f"Không tìm thấy mã nguồn RAG tại {RAG_ROOT}")

rag_path = str(RAG_ROOT)
if rag_path not in sys.path:
    sys.path.insert(0, rag_path)

# The embedded RAG service validates the same access token without making an
# HTTP request back into its own uvicorn process.
os.environ["AUTH_SERVICE_URL"] = "inprocess://backend"

from app.main import app as rag_app  # noqa: E402
from app.knowledge.crawler.scheduler import run_scheduler  # noqa: E402
from app.knowledge.crawler.worker import run_worker  # noqa: E402
from app.knowledge.pipeline_worker import run_pipeline_worker  # noqa: E402

logger = logging.getLogger(__name__)


async def _supervise(name: str, worker) -> None:
    """Keep one background component alive without taking down the API."""
    from src.config import settings
    while True:
        try:
            await worker()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("RAG background component crashed; restarting", extra={"component": name})
            await asyncio.sleep(settings.RAG_CRAWLER_RESTART_DELAY_SECONDS)


@asynccontextmanager
async def rag_lifespan() -> AsyncIterator[None]:
    """Start and stop RAG resources together with the main FastAPI app."""
    from src.config import settings
    async with rag_app.router.lifespan_context(rag_app):
        tasks: list[asyncio.Task] = []
        if settings.RAG_CRAWLER_BACKGROUND_ENABLED:
            tasks = [
                asyncio.create_task(_supervise("crawl-scheduler", run_scheduler), name="crawl-scheduler"),
                asyncio.create_task(_supervise("crawl-worker", run_worker), name="crawl-worker"),
                asyncio.create_task(_supervise("pipeline-worker", run_pipeline_worker), name="pipeline-worker"),
            ]
            logger.info("Embedded RAG crawler background services started")
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info("Embedded RAG crawler background services stopped")


def get_rag_app() -> FastAPI:
    return rag_app
