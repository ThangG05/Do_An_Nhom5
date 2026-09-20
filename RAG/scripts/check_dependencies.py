"""Check configured infrastructure without printing credentials or endpoints."""
import asyncio

from app.services.database import check_database
from app.services.qdrant import check_qdrant, close_qdrant
from app.services.redis import check_redis, close_redis
from app.db.session import dispose_engine


async def main() -> None:
    checks = {
        "database": check_database,
        "qdrant": check_qdrant,
        "redis": check_redis,
    }
    failed = False
    for name, check in checks.items():
        try:
            await check()
            print(f"{name}=ok")
        except Exception as exc:
            failed = True
            print(f"{name}=error ({type(exc).__name__})")
    await close_qdrant()
    await close_redis()
    await dispose_engine()
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
