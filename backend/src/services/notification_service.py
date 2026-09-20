import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from src.db.models.media import MediaFile, MediaStatus
from src.db.models.notification import Notification, NotificationType
from src.db.models.user import User
from src.models.notification import NotificationPageResponse, NotificationResponse
from src.services.storage_service import create_download_url


def _link(item: Notification) -> str | None:
    if item.reference_type == "POST" and item.reference_id:
        return f"/home?post={item.reference_id}"
    if item.reference_type == "USER" and item.reference_id:
        return f"/profile/{item.reference_id}"
    if item.type == NotificationType.FRIEND_REQUEST and item.actor_id:
        return f"/profile/{item.actor_id}"
    if item.type == NotificationType.MESSAGE:
        return f"/messages?conversationId={item.reference_id}" if item.reference_type == "CONVERSATION" and item.reference_id else "/messages"
    return None


def _serialize(db: Session, item: Notification) -> NotificationResponse:
    actor = db.get(User, item.actor_id) if item.actor_id else None
    avatar = None
    if actor and actor.profile and actor.profile.avatar_media_id:
        media = db.get(MediaFile, actor.profile.avatar_media_id)
        if media and media.status == MediaStatus.READY:
            avatar = create_download_url(media)
    return NotificationResponse(id=item.id, type=item.type.value, title=item.title, content=item.content or "", actor_id=item.actor_id, actor_name=actor.profile.full_name if actor and actor.profile else actor.username if actor else "HVNH Hub", actor_avatar=avatar, reference_type=item.reference_type, reference_id=item.reference_id, link=_link(item), is_unread=item.read_at is None, created_at=item.created_at)


def list_notifications(db: Session, user: User, limit: int, offset: int, unread_only: bool = False, friend_only: bool = False) -> NotificationPageResponse:
    filters = [Notification.user_id == user.id]
    if unread_only:
        filters.append(Notification.read_at.is_(None))
    if friend_only:
        filters.append(Notification.type == NotificationType.FRIEND_REQUEST)
    total = db.scalar(select(func.count()).select_from(Notification).where(*filters)) or 0
    unread = db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))) or 0
    rows = db.scalars(select(Notification).where(*filters).order_by(Notification.created_at.desc()).limit(limit).offset(offset)).all()
    return NotificationPageResponse(items=[_serialize(db, item) for item in rows], total=total, unread_count=unread, limit=limit, offset=offset)


def unread_count(db: Session, user_id: uuid.UUID) -> int:
    return db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user_id, Notification.read_at.is_(None))) or 0


def set_read(db: Session, user: User, notification_id: uuid.UUID, is_read: bool) -> Notification:
    item = db.get(Notification, notification_id)
    if not item or item.user_id != user.id:
        raise HTTPException(404, "Không tìm thấy thông báo.")
    item.read_at = datetime.now(timezone.utc) if is_read else None
    db.commit()
    db.refresh(item)
    return item


def mark_all_read(db: Session, user_id: uuid.UUID) -> None:
    db.execute(update(Notification).where(Notification.user_id == user_id, Notification.read_at.is_(None)).values(read_at=datetime.now(timezone.utc)))
    db.commit()


def delete_notification(db: Session, user: User, notification_id: uuid.UUID) -> None:
    item = db.get(Notification, notification_id)
    if not item or item.user_id != user.id:
        raise HTTPException(404, "Không tìm thấy thông báo.")
    db.delete(item)
    db.commit()
