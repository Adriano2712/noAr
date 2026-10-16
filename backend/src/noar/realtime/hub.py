import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

from noar.domain.enums import MonitorState

logger = logging.getLogger("noar.realtime")

CHANNEL = "monitor_events"

# Bounded so one stalled subscriber can't grow memory without limit; a slow
# consumer just misses events past this, rather than blocking the publisher.
QUEUE_MAXSIZE = 100


@dataclass(frozen=True)
class MonitorEvent:
    monitor_id: uuid.UUID
    owner_id: uuid.UUID
    is_public: bool
    state: MonitorState


class EventHub:
    """In-process fan-out from the Postgres LISTEN task to connected SSE clients.

    One instance per API process; each process also runs its own LISTEN
    connection (see realtime/listener.py), so this never needs to know
    about other processes -- Postgres NOTIFY already reaches every listener.
    """

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[MonitorEvent]] = set()

    def publish(self, event: MonitorEvent) -> None:
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("dropping event for a slow SSE subscriber")

    async def subscribe(self) -> AsyncIterator[MonitorEvent]:
        queue: asyncio.Queue[MonitorEvent] = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
        self._subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.discard(queue)


hub = EventHub()
