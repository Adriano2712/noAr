import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    telegram_chat_id: str | None
    webhook_url: str | None
    created_at: datetime


class NotificationSettingsUpdate(BaseModel):
    telegram_chat_id: str | None = Field(default=None, max_length=100)
    webhook_url: HttpUrl | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
