import asyncio
import os
import uuid

from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from noar.api.dependencies import get_current_user_from_query_token
from noar.api.routers.realtime import _event_stream
from noar.core.config import Settings
from noar.core.security import create_access_token
from noar.db.models import User
from noar.domain.enums import MonitorState
from noar.realtime.hub import EventHub, MonitorEvent


async def test_monitors_stream_requires_a_token(client: AsyncClient) -> None:
    response = await client.get("/monitors/stream")
    assert response.status_code == 422


async def test_monitors_stream_rejects_an_invalid_token(client: AsyncClient) -> None:
    response = await client.get("/monitors/stream", params={"token": "not-a-real-token"})
    assert response.status_code == 401


async def test_query_token_dependency_resolves_a_valid_token(db_engine: AsyncEngine) -> None:
    # This is the exact dependency `/monitors/stream` authenticates with; it's
    # exercised directly rather than through a real request to that route,
    # since httpx's ASGITransport only returns once the whole response
    # completes and this endpoint's stream never does. The route's rejection
    # paths (missing/invalid token) are still covered end-to-end above,
    # because those fail before any streaming body is produced.
    #
    # It also opens its own DB session rather than reusing one handed to it
    # (see dependencies.py), so this needs a *committed* user -- the usual
    # `client`/`db_session` fixtures roll back at the end of the test and
    # would be invisible to that separate connection.
    settings = Settings(  # type: ignore[call-arg]
        database_url=os.environ["DATABASE_URL"], api_secret_key=os.environ["API_SECRET_KEY"]
    )
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        user = User(email=f"{uuid.uuid4()}@example.com")
        session.add(user)
        await session.commit()
        user_id = user.id

    try:
        token = create_access_token(
            subject=str(user_id), secret_key=settings.api_secret_key, expires_minutes=60
        )

        resolved = await get_current_user_from_query_token(token, settings)

        assert resolved.id == user_id
    finally:
        async with session_factory() as session:
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()


def _event(**overrides: object) -> MonitorEvent:
    defaults: dict[str, object] = dict(
        monitor_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        is_public=False,
        state=MonitorState.UP,
    )
    defaults.update(overrides)
    return MonitorEvent(**defaults)  # type: ignore[arg-type]


async def test_event_stream_only_yields_events_for_the_given_owner() -> None:
    hub = EventHub()
    owner_id = uuid.uuid4()
    mine = _event(owner_id=owner_id)
    someone_elses = _event(owner_id=uuid.uuid4())

    stream = _event_stream(hub, owner_id, public_only=False)
    task = asyncio.ensure_future(anext(stream))
    await asyncio.sleep(0)

    hub.publish(someone_elses)
    hub.publish(mine)

    line = await asyncio.wait_for(task, timeout=1)
    assert str(mine.monitor_id) in line
    assert str(someone_elses.monitor_id) not in line


async def test_event_stream_with_public_only_skips_private_events() -> None:
    hub = EventHub()
    owner_id = uuid.uuid4()
    private = _event(owner_id=owner_id, is_public=False)
    public = _event(owner_id=owner_id, is_public=True)

    stream = _event_stream(hub, owner_id, public_only=True)
    task = asyncio.ensure_future(anext(stream))
    await asyncio.sleep(0)

    hub.publish(private)
    hub.publish(public)

    line = await asyncio.wait_for(task, timeout=1)
    assert str(public.monitor_id) in line
    assert str(private.monitor_id) not in line


async def test_event_stream_formats_as_server_sent_events() -> None:
    hub = EventHub()
    owner_id = uuid.uuid4()
    event = _event(owner_id=owner_id, state=MonitorState.DOWN)

    stream = _event_stream(hub, owner_id, public_only=False)
    task = asyncio.ensure_future(anext(stream))
    await asyncio.sleep(0)
    hub.publish(event)
    line = await asyncio.wait_for(task, timeout=1)

    assert line.startswith("data: ")
    assert line.endswith("\n\n")
    assert str(event.monitor_id) in line
    assert "down" in line
