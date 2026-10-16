import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from noar.api.dependencies import get_current_user
from noar.api.schemas.history import CheckRead, IncidentRead
from noar.api.schemas.monitors import MonitorCreate, MonitorRead, MonitorUpdate
from noar.api.validation import validate_outbound_url
from noar.core.config import Settings, get_settings
from noar.db.models import Check, Incident, Monitor, User
from noar.db.session import get_session
from noar.domain.enums import MonitorState

router = APIRouter(prefix="/monitors", tags=["monitors"])


async def _get_owned_monitor(
    monitor_id: uuid.UUID, current_user: User, session: AsyncSession
) -> Monitor:
    monitor = await session.get(Monitor, monitor_id)
    if monitor is None or monitor.owner_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "monitor not found")
    return monitor


@router.post("", response_model=MonitorRead, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    payload: MonitorCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Monitor:
    url = str(payload.url)
    await validate_outbound_url(url, settings)

    monitor = Monitor(
        owner_id=current_user.id,
        name=payload.name,
        url=url,
        interval_seconds=payload.interval_seconds,
        timeout_seconds=payload.timeout_seconds,
        fail_threshold=payload.fail_threshold,
    )
    session.add(monitor)
    await session.commit()
    await session.refresh(monitor)
    return monitor


@router.get("", response_model=list[MonitorRead])
async def list_monitors(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Monitor]:
    result = await session.scalars(
        select(Monitor).where(Monitor.owner_id == current_user.id).order_by(Monitor.created_at)
    )
    return list(result.all())


@router.get("/{monitor_id}", response_model=MonitorRead)
async def get_monitor(
    monitor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Monitor:
    return await _get_owned_monitor(monitor_id, current_user, session)


@router.patch("/{monitor_id}", response_model=MonitorRead)
async def update_monitor(
    monitor_id: uuid.UUID,
    payload: MonitorUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Monitor:
    monitor = await _get_owned_monitor(monitor_id, current_user, session)

    updates = payload.model_dump(exclude_unset=True)
    if "url" in updates:
        url = str(updates["url"])
        await validate_outbound_url(url, settings)
        updates["url"] = url

    for field, value in updates.items():
        setattr(monitor, field, value)

    await session.commit()
    await session.refresh(monitor)
    return monitor


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    monitor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    monitor = await _get_owned_monitor(monitor_id, current_user, session)
    await session.delete(monitor)
    await session.commit()


@router.post("/{monitor_id}/pause", response_model=MonitorRead)
async def pause_monitor(
    monitor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Monitor:
    monitor = await _get_owned_monitor(monitor_id, current_user, session)
    monitor.state = MonitorState.PAUSED
    await session.commit()
    await session.refresh(monitor)
    return monitor


@router.post("/{monitor_id}/resume", response_model=MonitorRead)
async def resume_monitor(
    monitor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Monitor:
    monitor = await _get_owned_monitor(monitor_id, current_user, session)
    monitor.state = MonitorState.UNKNOWN
    monitor.consecutive_failures = 0
    monitor.consecutive_successes = 0
    monitor.next_check_at = None
    await session.commit()
    await session.refresh(monitor)
    return monitor


@router.get("/{monitor_id}/checks", response_model=list[CheckRead])
async def list_checks(
    monitor_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Check]:
    await _get_owned_monitor(monitor_id, current_user, session)
    result = await session.scalars(
        select(Check)
        .where(Check.monitor_id == monitor_id)
        .order_by(Check.started_at.desc())
        .limit(limit)
    )
    return list(result.all())


@router.get("/{monitor_id}/incidents", response_model=list[IncidentRead])
async def list_incidents(
    monitor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Incident]:
    await _get_owned_monitor(monitor_id, current_user, session)
    result = await session.scalars(
        select(Incident)
        .where(Incident.monitor_id == monitor_id)
        .order_by(Incident.started_at.desc())
    )
    return list(result.all())
