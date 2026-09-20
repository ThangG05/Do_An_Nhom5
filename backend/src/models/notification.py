import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    content: str
    actor_id: uuid.UUID | None = None
    actor_name: str
    actor_avatar: str | None = None
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None
    link: str | None = None
    is_unread: bool
    created_at: datetime


class NotificationPageResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    limit: int
    offset: int


class NotificationCountResponse(BaseModel):
    unread_count: int


class NotificationReadRequest(BaseModel):
    is_read: bool = True


class MessageResponse(BaseModel):
    message: str
