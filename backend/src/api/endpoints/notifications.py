import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from src.api.dependencies import CurrentUser
from src.db.session import get_db
from src.models.notification import MessageResponse, NotificationCountResponse, NotificationPageResponse, NotificationReadRequest, NotificationResponse
from src.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationPageResponse)
def get_notifications(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)], limit: Annotated[int, Query(ge=1, le=100)] = 30, offset: Annotated[int, Query(ge=0)] = 0, unread_only: bool = False, friend_only: bool = False):
    return notification_service.list_notifications(db, current_user, limit, offset, unread_only, friend_only)


@router.get("/unread-count", response_model=NotificationCountResponse)
def get_unread_count(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    return NotificationCountResponse(unread_count=notification_service.unread_count(db, current_user.id))


@router.patch("/{notification_id}", response_model=NotificationResponse)
def change_read_status(notification_id: uuid.UUID, payload: NotificationReadRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    item = notification_service.set_read(db, current_user, notification_id, payload.is_read)
    return notification_service._serialize(db, item)


@router.post("/read-all", response_model=MessageResponse)
def read_all(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    notification_service.mark_all_read(db, current_user.id)
    return MessageResponse(message="Đã đánh dấu tất cả thông báo là đã đọc.")


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_notification(notification_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    notification_service.delete_notification(db, current_user, notification_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
