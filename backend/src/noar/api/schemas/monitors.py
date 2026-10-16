import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from noar.domain.enums import MonitorState


class MonitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    url: HttpUrl
    interval_seconds: int = Field(default=60, ge=10, le=86400)
    timeout_seconds: int = Field(default=10, ge=1, le=60)
    fail_threshold: int = Field(default=3, ge=1, le=20)


class MonitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    url: HttpUrl | None = None
    interval_seconds: int | None = Field(default=None, ge=10, le=86400)
    timeout_seconds: int | None = Field(default=None, ge=1, le=60)
    fail_threshold: int | None = Field(default=None, ge=1, le=20)
    is_public: bool | None = None


class MonitorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    url: str
    interval_seconds: int
    timeout_seconds: int
    fail_threshold: int
    state: MonitorState
    consecutive_failures: int
    consecutive_successes: int
    is_public: bool
    created_at: datetime
    updated_at: datetime
