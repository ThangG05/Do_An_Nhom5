from sqlalchemy import text

from app.db.session import AsyncSessionLocal, get_db


async def check_database() -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))


__all__ = ["AsyncSessionLocal", "check_database", "get_db"]
