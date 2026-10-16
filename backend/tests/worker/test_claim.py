import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from noar.db.models import Monitor, User
from noar.domain.enums import MonitorState
from noar.worker.claim import claim_due_monitors

PAST = datetime.now(UTC) - timedelta(seconds=1)
FUTURE = datetime.now(UTC) + timedelta(hours=1)


@pytest.fixture
async def owner(db_session: AsyncSession) -> AsyncGenerator[User, None]:
    user = User(email=f"{uuid.uuid4()}@example.com")
    db_session.add(user)
    await db_session.flush()
    yield user


def _monitor(owner_id: uuid.UUID, **overrides: object) -> Monitor:
    defaults: dict[str, object] = dict(
        owner_id=owner_id,
        name="test monitor",
        url="https://example.com",
        next_check_at=PAST,
    )
    defaults.update(overrides)
    return Monitor(**defaults)  # type: ignore[arg-type]


async def test_claims_a_due_monitor_and_sets_the_lease(
    db_session: AsyncSession, owner: User
) -> None:
    monitor = _monitor(owner.id)
    db_session.add(monitor)
    await db_session.flush()

    # limit=1000 and asserting by id, not by exact list equality: this reuses
    # the dev database (see tests/conftest.py), which can already have other
    # due monitors sitting in it from manual/e2e runs.
    claimed = await claim_due_monitors(db_session, limit=1000, lease_seconds=60)

    assert monitor.id in {m.id for m in claimed}
    assert monitor.locked_until is not None
    assert monitor.locked_until > datetime.now(UTC)


async def test_does_not_claim_a_monitor_scheduled_in_the_future(
    db_session: AsyncSession, owner: User
) -> None:
    monitor = _monitor(owner.id, next_check_at=FUTURE)
    db_session.add(monitor)
    await db_session.flush()

    claimed = await claim_due_monitors(db_session, limit=1000, lease_seconds=60)

    assert monitor.id not in {m.id for m in claimed}


async def test_does_not_claim_a_paused_monitor(db_session: AsyncSession, owner: User) -> None:
    monitor = _monitor(owner.id, state=MonitorState.PAUSED)
    db_session.add(monitor)
    await db_session.flush()

    claimed = await claim_due_monitors(db_session, limit=1000, lease_seconds=60)

    assert monitor.id not in {m.id for m in claimed}


async def test_does_not_reclaim_a_monitor_under_an_active_lease(
    db_session: AsyncSession, owner: User
) -> None:
    monitor = _monitor(owner.id, locked_until=FUTURE)
    db_session.add(monitor)
    await db_session.flush()

    claimed = await claim_due_monitors(db_session, limit=1000, lease_seconds=60)

    assert monitor.id not in {m.id for m in claimed}


async def test_reclaims_a_monitor_once_its_lease_expired(
    db_session: AsyncSession, owner: User
) -> None:
    monitor = _monitor(owner.id, locked_until=PAST)
    db_session.add(monitor)
    await db_session.flush()

    claimed = await claim_due_monitors(db_session, limit=1000, lease_seconds=60)

    assert monitor.id in {m.id for m in claimed}


async def test_respects_the_batch_limit(db_session: AsyncSession, owner: User) -> None:
    db_session.add_all(_monitor(owner.id) for _ in range(5))
    await db_session.flush()

    claimed = await claim_due_monitors(db_session, limit=2, lease_seconds=60)

    assert len(claimed) == 2


async def test_concurrent_claims_never_overlap_or_drop_a_monitor(db_engine: AsyncEngine) -> None:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async with session_factory() as setup_session:
        owner_row = User(email=f"{uuid.uuid4()}@example.com")
        setup_session.add(owner_row)
        await setup_session.flush()
        monitors = [_monitor(owner_row.id) for _ in range(6)]
        setup_session.add_all(monitors)
        await setup_session.commit()
        owner_id = owner_row.id
        monitor_ids = {m.id for m in monitors}

    try:

        async def claim() -> list[Monitor]:
            async with session_factory() as session:
                return await claim_due_monitors(session, limit=10, lease_seconds=60)

        batch_a, batch_b = await asyncio.gather(claim(), claim())
        claimed_ids = [
            m.id for batch in (batch_a, batch_b) for m in batch if m.id in monitor_ids
        ]

        assert len(claimed_ids) == len(monitor_ids)
        assert len(set(claimed_ids)) == len(claimed_ids)
    finally:
        async with session_factory() as cleanup_session:
            await cleanup_session.execute(delete(Monitor).where(Monitor.owner_id == owner_id))
            await cleanup_session.execute(delete(User).where(User.id == owner_id))
            await cleanup_session.commit()
