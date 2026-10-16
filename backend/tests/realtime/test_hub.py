import asyncio
import uuid

from noar.domain.enums import MonitorState
from noar.realtime.hub import QUEUE_MAXSIZE, EventHub, MonitorEvent


def _event(**overrides: object) -> MonitorEvent:
    defaults: dict[str, object] = dict(
        monitor_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        is_public=False,
        state=MonitorState.UP,
    )
    defaults.update(overrides)
    return MonitorEvent(**defaults)  # type: ignore[arg-type]


async def test_a_subscriber_receives_a_published_event() -> None:
    hub = EventHub()
    subscription = hub.subscribe()

    # anext() only registers the subscriber once it actually runs; give the
    # event loop a tick so the generator reaches its first `await queue.get()`.
    task = asyncio.ensure_future(anext(subscription))
    await asyncio.sleep(0)

    event = _event()
    hub.publish(event)

    assert await asyncio.wait_for(task, timeout=1) == event


async def test_publish_fans_out_to_every_subscriber() -> None:
    hub = EventHub()
    first = hub.subscribe()
    second = hub.subscribe()

    first_task = asyncio.ensure_future(anext(first))
    second_task = asyncio.ensure_future(anext(second))
    await asyncio.sleep(0)

    event = _event()
    hub.publish(event)

    assert await asyncio.wait_for(first_task, timeout=1) == event
    assert await asyncio.wait_for(second_task, timeout=1) == event


async def test_publish_with_no_subscribers_does_not_raise() -> None:
    hub = EventHub()
    hub.publish(_event())


async def test_a_full_queue_drops_the_newest_event_instead_of_raising() -> None:
    hub = EventHub()
    subscription = hub.subscribe()
    task = asyncio.ensure_future(anext(subscription))
    await asyncio.sleep(0)

    # None of these are awaited in between, so they pile up in the queue
    # instead of being drained by `task`; the last one overflows it.
    events = [_event() for _ in range(QUEUE_MAXSIZE + 1)]
    for event in events:
        hub.publish(event)

    assert await asyncio.wait_for(task, timeout=1) == events[0]


async def test_unsubscribing_removes_the_queue_from_the_hub() -> None:
    hub = EventHub()
    subscription = hub.subscribe()

    task = asyncio.ensure_future(anext(subscription))
    await asyncio.sleep(0)
    assert len(hub._subscribers) == 1

    hub.publish(_event())
    await task

    await subscription.aclose()
    assert len(hub._subscribers) == 0
