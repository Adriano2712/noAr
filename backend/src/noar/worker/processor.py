import random
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from noar.alerts.dispatch import dispatch_alert
from noar.alerts.events import AlertContext, AlertEvent
from noar.core.config import Settings
from noar.db.models import Check, Incident, Monitor, User
from noar.domain.monitor_state import MonitorSnapshot, evaluate_check
from noar.realtime.notify import publish_monitor_event
from noar.worker.checker import run_http_check

DispatchFn = Callable[[User, AlertContext, Settings, httpx.AsyncClient], Awaitable[None]]
NotifyFn = Callable[[AsyncSession, Monitor], Awaitable[None]]


async def process_monitor(
    session: AsyncSession,
    monitor: Monitor,
    client: httpx.AsyncClient,
    settings: Settings,
    *,
    dispatch: DispatchFn = dispatch_alert,
    notify: NotifyFn = publish_monitor_event,
) -> None:
    """Run one check for `monitor`, apply the state machine, and persist everything.

    Releases the scheduling lease and reschedules the monitor on every path,
    including when the check itself fails, so a flaky target never gets
    stuck unscheduled. `dispatch` and `notify` are injectable so tests don't
    make real network/NOTIFY calls; production code uses the real ones.
    """
    started_at = datetime.now(UTC)
    outcome = await run_http_check(
        client,
        monitor.url,
        timeout_seconds=monitor.timeout_seconds,
        allow_private=settings.ssrf_allow_private_networks,
    )
    finished_at = datetime.now(UTC)

    session.add(
        Check(
            monitor_id=monitor.id,
            started_at=started_at,
            finished_at=finished_at,
            success=outcome.success,
            status_code=outcome.status_code,
            response_time_ms=outcome.response_time_ms,
            error_message=outcome.error_message,
        )
    )

    snapshot = MonitorSnapshot(
        state=monitor.state,
        consecutive_failures=monitor.consecutive_failures,
        consecutive_successes=monitor.consecutive_successes,
        fail_threshold=monitor.fail_threshold,
    )
    evaluation = evaluate_check(snapshot, outcome.success)

    monitor.state = evaluation.snapshot.state
    monitor.consecutive_failures = evaluation.snapshot.consecutive_failures
    monitor.consecutive_successes = evaluation.snapshot.consecutive_successes

    alert_context: AlertContext | None = None

    if evaluation.opened_incident:
        session.add(Incident(monitor_id=monitor.id, started_at=finished_at))
        alert_context = AlertContext(
            event=AlertEvent.INCIDENT_OPENED,
            monitor_name=monitor.name,
            monitor_url=monitor.url,
            incident_started_at=finished_at,
            incident_resolved_at=None,
        )

    if evaluation.closed_incident:
        open_incident = await session.scalar(
            select(Incident)
            .where(Incident.monitor_id == monitor.id, Incident.resolved_at.is_(None))
            .order_by(Incident.started_at.desc())
            .limit(1)
        )
        if open_incident is not None:
            open_incident.resolved_at = finished_at
            alert_context = AlertContext(
                event=AlertEvent.INCIDENT_CLOSED,
                monitor_name=monitor.name,
                monitor_url=monitor.url,
                incident_started_at=open_incident.started_at,
                incident_resolved_at=finished_at,
            )

    jitter_seconds = monitor.interval_seconds * settings.scheduler_jitter_fraction * (
        2 * random.random() - 1
    )
    monitor.next_check_at = finished_at + timedelta(
        seconds=monitor.interval_seconds + jitter_seconds
    )
    monitor.locked_until = None

    state_changed = evaluation.snapshot.state != snapshot.state

    await session.commit()

    if state_changed:
        await notify(session, monitor)

    if alert_context is not None:
        owner = await session.get(User, monitor.owner_id)
        if owner is not None:
            await dispatch(owner, alert_context, settings, client)
