import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from noar.db.models import Monitor
from noar.realtime.hub import CHANNEL


async def publish_monitor_event(session: AsyncSession, monitor: Monitor) -> None:
    """Notify any listening API process that `monitor`'s state changed.

    Runs its own transaction: NOTIFY is only delivered to listeners once the
    issuing transaction commits, and by the time this runs the check itself
    has already committed separately, so there's nothing to batch it with.
    """
    payload = json.dumps(
        {
            "monitor_id": str(monitor.id),
            "owner_id": str(monitor.owner_id),
            "is_public": monitor.is_public,
            "state": monitor.state.value,
        }
    )
    await session.execute(
        text("SELECT pg_notify(:channel, :payload)"), {"channel": CHANNEL, "payload": payload}
    )
    await session.commit()
