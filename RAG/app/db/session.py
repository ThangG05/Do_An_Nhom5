from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.sqlalchemy_database_uri, echo=settings.db_echo,
                             pool_pre_ping=True, pool_size=settings.db_pool_size,
                             max_overflow=settings.db_max_overflow,
                             pool_recycle=settings.db_pool_recycle_seconds,
                             connect_args={"command_timeout": settings.db_command_timeout_seconds})
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    await engine.dispose()
