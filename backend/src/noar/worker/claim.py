from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from noar.db.models import Monitor
from noar.domain.enums import MonitorState


async def claim_due_monitors(
    session: AsyncSession, *, limit: int, lease_seconds: int
) -> list[Monitor]:
    """Atomically claim up to `limit` due monitors for this worker.

    Uses `SELECT ... FOR UPDATE SKIP LOCKED` so multiple workers can run this
    concurrently without claiming the same monitor twice, and commits right
    after setting the lease so the Postgres row lock is held only for the
    claim itself, never for the slow HTTP check that follows (see ADR 0003).
    """
    now = datetime.now(UTC)
    lease_until = now + timedelta(seconds=lease_seconds)

    stmt = (
        select(Monitor)
        .where(Monitor.state != MonitorState.PAUSED)
        .where(or_(Monitor.next_check_at.is_(None), Monitor.next_check_at <= now))
        .where(or_(Monitor.locked_until.is_(None), Monitor.locked_until < now))
        .order_by(Monitor.next_check_at.asc().nulls_first())
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    result = await session.execute(stmt)
    monitors = list(result.scalars().all())

    for monitor in monitors:
        monitor.locked_until = lease_until

    await session.commit()
    return monitors
