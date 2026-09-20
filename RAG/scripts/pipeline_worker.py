import argparse
import asyncio
from uuid import UUID

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import dispose_engine
from app.knowledge.pipeline_worker import process_pipeline_run, run_pipeline_worker
from app.services.redis import close_redis


async def main(run_id: str | None) -> None:
    try:
        await (process_pipeline_run(UUID(run_id)) if run_id else run_pipeline_worker())
    finally:
        await close_redis()
        await dispose_engine()


if __name__ == "__main__":
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    parser = argparse.ArgumentParser(description="Run post-crawl OCR/chunk/index pipeline")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    asyncio.run(main(args.run_id))
