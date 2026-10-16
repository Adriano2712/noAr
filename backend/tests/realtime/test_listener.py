import asyncio
import contextlib
import json
import os
import uuid

import asyncpg

from noar.core.config import Settings
from noar.domain.enums import MonitorState
from noar.realtime.hub import CHANNEL, EventHub, MonitorEvent
from noar.realtime.listener import _asyncpg_dsn, run_listener

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", os.environ["DATABASE_URL"])
NOTIFY_TIMEOUT_SECONDS = 5


def _settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        database_url=TEST_DATABASE_URL,
        api_secret_key=os.environ["API_SECRET_KEY"],
    )


def _payload(event: MonitorEvent) -> str:
    return json.dumps(
        {
            "monitor_id": str(event.monitor_id),
            "owner_id": str(event.owner_id),
            "is_public": event.is_public,
            "state": event.state.value,
        }
    )


async def _notify_until_received(
    connection: asyncpg.Connection, receive_task: "asyncio.Task[MonitorEvent]", payload: str
) -> MonitorEvent:
    """Resend the NOTIFY until the listener task picks it up.

    `run_listener` needs a moment to connect and register its LISTEN after
    the task is created; a single pg_notify sent before that happens is
    simply lost (Postgres doesn't queue it for a listener that isn't there
    yet), so retrying is the robust way to wait rather than guessing a sleep.
    """
    async with asyncio.timeout(NOTIFY_TIMEOUT_SECONDS):
        while True:
            await connection.execute("SELECT pg_notify($1, $2)", CHANNEL, payload)
            with contextlib.suppress(TimeoutError):
                return await asyncio.wait_for(asyncio.shield(receive_task), timeout=0.2)


async def test_a_real_notify_reaches_the_hub() -> None:
    settings = _settings()
    dsn = _asyncpg_dsn(settings)
    hub = EventHub()

    listener_task = asyncio.create_task(run_listener(settings, hub))
    try:
        subscription = hub.subscribe()
        receive_task = asyncio.ensure_future(anext(subscription))
        await asyncio.sleep(0)

        event = MonitorEvent(
            monitor_id=uuid.uuid4(),
            owner_id=uuid.uuid4(),
            is_public=True,
            state=MonitorState.DOWN,
        )

        connection = await asyncpg.connect(dsn)
        try:
            received = await _notify_until_received(connection, receive_task, _payload(event))
        finally:
            await connection.close()

        assert received == event
    finally:
        listener_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await listener_task


async def test_a_malformed_payload_does_not_crash_the_listener() -> None:
    settings = _settings()
    dsn = _asyncpg_dsn(settings)
    hub = EventHub()

    listener_task = asyncio.create_task(run_listener(settings, hub))
    try:
        connection = await asyncpg.connect(dsn)
        try:
            # Garbage first: the listener should log and move on rather than
            # dying, so the well-formed notify right after still gets through.
            await connection.execute("SELECT pg_notify($1, $2)", CHANNEL, "not valid json")

            subscription = hub.subscribe()
            receive_task = asyncio.ensure_future(anext(subscription))
            await asyncio.sleep(0)

            event = MonitorEvent(
                monitor_id=uuid.uuid4(),
                owner_id=uuid.uuid4(),
                is_public=False,
                state=MonitorState.UP,
            )
            received = await _notify_until_received(connection, receive_task, _payload(event))
        finally:
            await connection.close()

        assert received == event
    finally:
        listener_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await listener_task
