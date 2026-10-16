import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from noar.api.dependencies import get_current_user_from_query_token
from noar.db.models import User
from noar.realtime.hub import EventHub, MonitorEvent, hub

router = APIRouter(tags=["realtime"])


def _format(event: MonitorEvent) -> str:
    payload = json.dumps({"monitor_id": str(event.monitor_id), "state": event.state.value})
    return f"data: {payload}\n\n"


async def _event_stream(
    event_hub: EventHub, owner_id: uuid.UUID, *, public_only: bool
) -> AsyncIterator[str]:
    async for event in event_hub.subscribe():
        if event.owner_id != owner_id:
            continue
        if public_only and not event.is_public:
            continue
        yield _format(event)


@router.get("/monitors/stream")
async def stream_my_monitors(
    current_user: User = Depends(get_current_user_from_query_token),
) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(hub, current_user.id, public_only=False),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/status/{owner_id}/stream")
async def stream_status(owner_id: uuid.UUID) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(hub, owner_id, public_only=True),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
