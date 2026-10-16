import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    started_at: datetime
    finished_at: datetime
    success: bool
    status_code: int | None
    response_time_ms: int | None
    error_message: str | None


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    started_at: datetime
    resolved_at: datetime | None
