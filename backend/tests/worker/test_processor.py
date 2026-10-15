import uuid
from collections.abc import AsyncGenerator

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from noar.db.models import Check, Incident, Monitor, User
from noar.domain.enums import MonitorState
from noar.worker.processor import process_monitor


@pytest.fixture
async def owner(db_session: AsyncSession) -> AsyncGenerator[User, None]:
    user = User(email=f"{uuid.uuid4()}@example.com")
    db_session.add(user)
    await db_session.flush()
    yield user


@pytest.fixture
async def monitor(db_session: AsyncSession, owner: User) -> AsyncGenerator[Monitor, None]:
    row = Monitor(
        owner_id=owner.id,
        name="test monitor",
        url="https://example.com",
        fail_threshold=2,
    )
    db_session.add(row)
    await db_session.flush()
    yield row


# allow_private=True below only skips the SSRF guard's DNS lookup, so these
# tests don't depend on real network access; the guard itself is covered in
# tests/security/test_ssrf.py and tests/worker/test_checker.py.
def _client(status_code: int) -> httpx.AsyncClient:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def _open_incident(session: AsyncSession, monitor_id: uuid.UUID) -> Incident | None:
    return await session.scalar(
        select(Incident).where(Incident.monitor_id == monitor_id, Incident.resolved_at.is_(None))
    )


async def test_successful_check_moves_unknown_monitor_to_up(
    db_session: AsyncSession, monitor: Monitor
) -> None:
    async with _client(200) as client:
        await process_monitor(
            db_session, monitor, client, allow_private=True, jitter_fraction=0.0
        )

    assert monitor.state is MonitorState.UP
    assert monitor.locked_until is None
    assert monitor.next_check_at is not None

    checks = (await db_session.scalars(select(Check).where(Check.monitor_id == monitor.id))).all()
    assert len(checks) == 1
    assert checks[0].success is True


async def test_reaching_fail_threshold_opens_an_incident(
    db_session: AsyncSession, monitor: Monitor
) -> None:
    async with _client(500) as client:
        await process_monitor(
            db_session, monitor, client, allow_private=True, jitter_fraction=0.0
        )
        await process_monitor(
            db_session, monitor, client, allow_private=True, jitter_fraction=0.0
        )

    assert monitor.state is MonitorState.DOWN
    incident = await _open_incident(db_session, monitor.id)
    assert incident is not None


async def test_recovering_after_an_incident_resolves_it(
    db_session: AsyncSession, monitor: Monitor
) -> None:
    async with _client(500) as client:
        await process_monitor(
            db_session, monitor, client, allow_private=True, jitter_fraction=0.0
        )
        await process_monitor(
            db_session, monitor, client, allow_private=True, jitter_fraction=0.0
        )

    assert monitor.state is MonitorState.DOWN

    async with _client(200) as client:
        await process_monitor(
            db_session, monitor, client, allow_private=True, jitter_fraction=0.0
        )

    assert monitor.state is MonitorState.UP
    assert await _open_incident(db_session, monitor.id) is None

    resolved = await db_session.scalar(select(Incident).where(Incident.monitor_id == monitor.id))
    assert resolved is not None
    assert resolved.resolved_at is not None
