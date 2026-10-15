import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from noar.db.base import Base
from noar.domain.enums import MonitorState


class Monitor(Base):
    __tablename__ = "monitors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    name: Mapped[str]
    url: Mapped[str]

    interval_seconds: Mapped[int] = mapped_column(default=60)
    timeout_seconds: Mapped[int] = mapped_column(default=10)
    fail_threshold: Mapped[int] = mapped_column(default=3)

    state: Mapped[MonitorState] = mapped_column(
        Enum(MonitorState, name="monitor_state"), default=MonitorState.UNKNOWN
    )
    consecutive_failures: Mapped[int] = mapped_column(default=0)
    consecutive_successes: Mapped[int] = mapped_column(default=0)

    # Scheduling lease (ADR 0003); the worker starts using these in a later phase.
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
