from sqlalchemy.ext.asyncio import AsyncSession

from noar.db.models import Monitor, User
from noar.domain.enums import MonitorState


async def test_create_monitor_for_owner(db_session: AsyncSession) -> None:
    owner = User(email="owner@example.com")
    db_session.add(owner)
    await db_session.flush()

    monitor = Monitor(owner_id=owner.id, name="Example", url="https://example.com")
    db_session.add(monitor)
    await db_session.flush()
    await db_session.refresh(monitor)

    assert monitor.id is not None
    assert monitor.owner_id == owner.id
    assert monitor.state is MonitorState.UNKNOWN
    assert monitor.consecutive_failures == 0
