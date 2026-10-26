import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from src.db.models.media import MediaFile, MediaStatus
from src.db.models.notification import Notification, NotificationType
from src.db.models.post import Comment
from src.db.models.user import Profile, User
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
    payload = dict(item.payload or {})
    # Notifications created before comment deep-linking only stored post_id.
    # Recover the most likely target so old records remain useful too.
    if item.type == NotificationType.COMMENT and "comment_id" not in payload and item.reference_id and item.actor_id:
        comment_id = db.scalar(select(Comment.id).where(Comment.post_id == item.reference_id, Comment.user_id == item.actor_id, Comment.deleted_at.is_(None)).order_by(Comment.created_at.desc()))
        if comment_id:
            payload["comment_id"] = str(comment_id)
            payload.setdefault("post_id", str(item.reference_id))
    return NotificationResponse(id=item.id, type=item.type.value, title=item.title, content=item.content or "", actor_id=item.actor_id, actor_name=actor.profile.full_name if actor and actor.profile else actor.username if actor else "HVNH Hub", actor_avatar=avatar, reference_type=item.reference_type, reference_id=item.reference_id, payload=payload, link=_link(item), is_unread=item.read_at is None, created_at=item.created_at)


def _serialize_many(db: Session, items: list[Notification]) -> list[NotificationResponse]:
    if not items:
        return []
    actor_ids = {item.actor_id for item in items if item.actor_id}
    actors = {user.id: user for user in db.scalars(select(User).where(User.id.in_(actor_ids))).all()} if actor_ids else {}
    profiles = {profile.user_id: profile for profile in db.scalars(select(Profile).where(Profile.user_id.in_(actor_ids))).all()} if actor_ids else {}
    avatar_ids = {profile.avatar_media_id for profile in profiles.values() if profile.avatar_media_id}
    avatars = {media.id: media for media in db.scalars(select(MediaFile).where(MediaFile.id.in_(avatar_ids), MediaFile.status == MediaStatus.READY)).all()} if avatar_ids else {}

    legacy = [item for item in items if item.type == NotificationType.COMMENT and item.reference_id and item.actor_id and "comment_id" not in (item.payload or {})]
    comment_ids: dict[tuple[uuid.UUID, uuid.UUID], uuid.UUID] = {}
    if legacy:
        post_ids = {item.reference_id for item in legacy}
        comment_actor_ids = {item.actor_id for item in legacy}
        rows = db.execute(select(Comment.post_id, Comment.user_id, Comment.id).where(
            Comment.post_id.in_(post_ids), Comment.user_id.in_(comment_actor_ids), Comment.deleted_at.is_(None)
        ).distinct(Comment.post_id, Comment.user_id).order_by(
            Comment.post_id, Comment.user_id, Comment.created_at.desc(), Comment.id.desc()
        )).all()
        for post_id, user_id, comment_id in rows:
            comment_ids[(post_id, user_id)] = comment_id

    result: list[NotificationResponse] = []
    for item in items:
        actor = actors.get(item.actor_id)
        profile = profiles.get(item.actor_id)
        avatar_media = avatars.get(profile.avatar_media_id) if profile and profile.avatar_media_id else None
        payload = dict(item.payload or {})
        if item.type == NotificationType.COMMENT and "comment_id" not in payload and item.reference_id and item.actor_id:
            comment_id = comment_ids.get((item.reference_id, item.actor_id))
            if comment_id:
                payload["comment_id"] = str(comment_id)
                payload.setdefault("post_id", str(item.reference_id))
        result.append(NotificationResponse(
            id=item.id, type=item.type.value, title=item.title, content=item.content or "",
            actor_id=item.actor_id, actor_name=profile.full_name if profile else actor.username if actor else "HVNH Hub",
            actor_avatar=create_download_url(avatar_media) if avatar_media else None,
            reference_type=item.reference_type, reference_id=item.reference_id, payload=payload,
            link=_link(item), is_unread=item.read_at is None, created_at=item.created_at,
        ))
    return result


def list_notifications(db: Session, user: User, limit: int, offset: int, unread_only: bool = False, friend_only: bool = False) -> NotificationPageResponse:
    # Tin nhắn có badge và màn hình riêng; không đưa MESSAGE vào trung tâm thông báo.
    filters = [Notification.user_id == user.id, Notification.type != NotificationType.MESSAGE]
    if unread_only:
        filters.append(Notification.read_at.is_(None))
    if friend_only:
        filters.append(Notification.type == NotificationType.FRIEND_REQUEST)
    total = db.scalar(select(func.count()).select_from(Notification).where(*filters)) or 0
    unread = db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user.id, Notification.type != NotificationType.MESSAGE, Notification.read_at.is_(None))) or 0
    rows = db.scalars(select(Notification).where(*filters).order_by(Notification.created_at.desc()).limit(limit).offset(offset)).all()
    return NotificationPageResponse(items=_serialize_many(db, rows), total=total, unread_count=unread, limit=limit, offset=offset)


def unread_count(db: Session, user_id: uuid.UUID) -> int:
    return db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user_id, Notification.type != NotificationType.MESSAGE, Notification.read_at.is_(None))) or 0


def header_unread_counts(db: Session, user_id: uuid.UUID) -> tuple[int, int]:
    """Read both navbar badges in one database round trip."""
    from src.db.models.chat import ConversationMember, Message, MessageReceipt

    notifications = select(func.count()).select_from(Notification).where(
        Notification.user_id == user_id,
        Notification.type != NotificationType.MESSAGE,
        Notification.read_at.is_(None),
    ).scalar_subquery()
    messages = select(func.count()).select_from(MessageReceipt).join(
        Message, Message.id == MessageReceipt.message_id,
    ).join(ConversationMember, (
        ConversationMember.conversation_id == Message.conversation_id
    ) & (ConversationMember.user_id == MessageReceipt.user_id)).where(
        MessageReceipt.user_id == user_id,
        MessageReceipt.seen_at.is_(None),
        Message.deleted_at.is_(None),
        ConversationMember.left_at.is_(None),
        ConversationMember.is_muted.is_(False),
    ).scalar_subquery()
    notification_count, message_count = db.execute(select(notifications, messages)).one()
    return notification_count, message_count


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
