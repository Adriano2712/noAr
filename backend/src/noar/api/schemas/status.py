import uuid

from pydantic import BaseModel

from noar.domain.enums import MonitorState


class PublicMonitorRead(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    state: MonitorState
    uptime_percentage: float | None


class StatusPageRead(BaseModel):
    monitors: list[PublicMonitorRead]
