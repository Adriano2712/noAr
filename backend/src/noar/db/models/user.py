import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from noar.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(unique=True, index=True)
    # Nullable: the demo user seeded before auth existed (scripts/seed_demo_monitor.py)
    # has no password and is not meant to log in through the API.
    hashed_password: Mapped[str | None] = mapped_column(default=None)

    # Alert destinations (Fase 6). Both optional: email (via the account's
    # own address) always applies, these two are opt-in extra channels.
    telegram_chat_id: Mapped[str | None] = mapped_column(default=None)
    webhook_url: Mapped[str | None] = mapped_column(default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
