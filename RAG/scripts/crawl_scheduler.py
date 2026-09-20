import argparse
import asyncio
import json

from app.db.session import dispose_engine
from app.knowledge.crawler.scheduler import run_scheduler, scheduler_once
from app.services.redis import close_redis


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Recover stale work and enqueue due sources once")
    args = parser.parse_args()
    try:
        if args.once:
            print(json.dumps(await scheduler_once()))
        else:
            await run_scheduler()
    finally:
        await close_redis()
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
