import asyncio
import argparse
from uuid import UUID
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import dispose_engine
from app.knowledge.crawler.worker import process_run, run_worker
from app.services.redis import close_redis


async def main(run_id: str | None) -> None:
    try:
        await (process_run(UUID(run_id)) if run_id else run_worker())
    finally:
        await close_redis()
        await dispose_engine()

if __name__ == "__main__":
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", help="process one Neon run directly, then exit")
    args = parser.parse_args()
    asyncio.run(main(args.run_id))
