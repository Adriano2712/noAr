import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from noar.api.schemas.status import PublicMonitorRead, StatusPageRead
from noar.db.models import Check, Monitor
from noar.db.session import get_session

router = APIRouter(prefix="/status", tags=["status"])

UPTIME_WINDOW = 100


async def _uptime_percentage(session: AsyncSession, monitor_id: uuid.UUID) -> float | None:
    recent_results = list(
        await session.scalars(
            select(Check.success)
            .where(Check.monitor_id == monitor_id)
            .order_by(Check.started_at.desc())
            .limit(UPTIME_WINDOW)
        )
    )
    if not recent_results:
        return None
    return round(sum(recent_results) / len(recent_results) * 100, 1)


@router.get("/{owner_id}", response_model=StatusPageRead)
async def get_status_page(
    owner_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> StatusPageRead:
    """Public, unauthenticated: an account's status page.

    Always 200, even for an owner_id with no public monitors or that
    doesn't exist -- an empty list either way, so this can't be used to
    probe which user IDs are real accounts.
    """
    monitors = list(
        await session.scalars(
            select(Monitor)
            .where(Monitor.owner_id == owner_id, Monitor.is_public.is_(True))
            .order_by(Monitor.name)
        )
    )

    public_monitors = [
        PublicMonitorRead(
            id=monitor.id,
            name=monitor.name,
            url=monitor.url,
            state=monitor.state,
            uptime_percentage=await _uptime_percentage(session, monitor.id),
        )
        for monitor in monitors
    ]
    return StatusPageRead(monitors=public_monitors)
