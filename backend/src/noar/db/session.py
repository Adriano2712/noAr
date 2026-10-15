from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from noar.core.config import get_settings


def build_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(str(settings.database_url), pool_pre_ping=True)


engine = build_engine()
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
