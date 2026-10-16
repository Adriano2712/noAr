import asyncio
import json
import logging
import uuid
from typing import Any

import asyncpg

from noar.core.config import Settings
from noar.domain.enums import MonitorState
from noar.realtime.hub import CHANNEL, EventHub, MonitorEvent

logger = logging.getLogger("noar.realtime")

RECONNECT_DELAY_SECONDS = 5
CONNECTION_CHECK_INTERVAL_SECONDS = 5


def _asyncpg_dsn(settings: Settings) -> str:
    # SQLAlchemy's "+asyncpg" dialect suffix isn't a scheme asyncpg.connect
    # understands on its own.
    return str(settings.database_url).replace("postgresql+asyncpg://", "postgresql://")


def _handle_notification(hub: EventHub, payload: str) -> None:
    try:
        data: dict[str, Any] = json.loads(payload)
        hub.publish(
            MonitorEvent(
                monitor_id=uuid.UUID(data["monitor_id"]),
                owner_id=uuid.UUID(data["owner_id"]),
                is_public=bool(data["is_public"]),
                state=MonitorState(data["state"]),
            )
        )
    except Exception:
        logger.exception("failed to handle NOTIFY payload: %r", payload)


async def run_listener(settings: Settings, hub: EventHub) -> None:
    """Keep a dedicated LISTEN connection open, reconnecting on failure.

    Runs for the lifetime of the API process (started from the FastAPI
    lifespan). A plain SQLAlchemy pooled connection can't be used for
    LISTEN: the pool may recycle it mid-stream, silently dropping
    notifications, so this talks to asyncpg directly instead.
    """
    dsn = _asyncpg_dsn(settings)
    while True:
        try:
            connection = await asyncpg.connect(dsn)
        except Exception:
            logger.exception(
                "failed to connect for LISTEN, retrying in %ss", RECONNECT_DELAY_SECONDS
            )
            await asyncio.sleep(RECONNECT_DELAY_SECONDS)
            continue

        try:
            await connection.add_listener(
                CHANNEL, lambda _conn, _pid, _channel, payload: _handle_notification(hub, payload)
            )
            logger.info("listening for monitor events on %r", CHANNEL)
            while not connection.is_closed():
                await asyncio.sleep(CONNECTION_CHECK_INTERVAL_SECONDS)
            logger.warning("LISTEN connection closed, reconnecting")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("LISTEN connection failed, reconnecting")
        finally:
            if not connection.is_closed():
                await connection.close()
