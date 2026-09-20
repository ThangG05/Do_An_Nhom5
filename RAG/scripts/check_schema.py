"""Read-only schema summary for the configured PostgreSQL database."""
import asyncio

from sqlalchemy import text

from app.db.session import engine


async def main() -> None:
    async with engine.connect() as connection:
        tables = (await connection.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        ))).scalars().all()
        enums = (await connection.execute(text(
            "SELECT typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace "
            "WHERE n.nspname = 'public' AND t.typtype = 'e' ORDER BY typname"
        ))).scalars().all()
    await engine.dispose()
    print(f"TABLE_COUNT={len(tables)}")
    print(f"TABLES={','.join(tables)}")
    print(f"ENUM_COUNT={len(enums)}")
    print(f"ENUMS={','.join(enums)}")


if __name__ == "__main__":
    asyncio.run(main())
