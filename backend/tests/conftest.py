import os

# Settings() requires these at import time (noar.api.main builds CORS from it),
# and tests otherwise run without any .env file at all.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://noar:noar_dev_password@localhost:5432/noar"
)
os.environ.setdefault("API_SECRET_KEY", "test-secret-key-at-least-32-bytes-long")

from collections.abc import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine  # noqa: E402

from noar.db.base import Base  # noqa: E402
from noar.db.models import Check, Incident, Monitor, User  # noqa: E402, F401

# Reuses the local docker compose `db` service by default. Tests that use
# `db_session` run inside a rolled-back transaction each, so they never leave
# data behind; tests that need real concurrency use `db_engine` directly and
# clean up their own rows (see tests/worker/test_claim.py).
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://noar:noar_dev_password@localhost:5432/noar",
)


@pytest.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with db_engine.connect() as connection:
        await connection.begin()
        session = AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        try:
            yield session
        finally:
            await session.close()
            await connection.rollback()
