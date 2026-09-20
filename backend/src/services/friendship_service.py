import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import delete, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models.friendship import FriendRequest, FriendRequestStatus, Friendship
from src.db.models.user import User
from src.models.user import FriendResponse
from src.services.user_service import _media_url, friendship_status


def _pair(first: uuid.UUID, second: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
    return tuple(sorted((first, second)))


def _pending(db: Session, first: uuid.UUID, second: uuid.UUID) -> FriendRequest | None:
    return db.scalar(select(FriendRequest).where(FriendRequest.status == FriendRequestStatus.PENDING, or_(
        (FriendRequest.sender_id == first) & (FriendRequest.receiver_id == second),
        (FriendRequest.sender_id == second) & (FriendRequest.receiver_id == first),
    )).with_for_update())


def relation_status(db: Session, viewer_id: uuid.UUID, target_id: uuid.UUID) -> str:
    status = friendship_status(db, viewer_id, target_id)
    if status != "none":
        return status
    request = _pending(db, viewer_id, target_id)
    if not request:
        return "none"
    return "pending_sent" if request.sender_id == viewer_id else "pending_received"


def act(db: Session, actor: User, target: User, action: str) -> str:
    from src.services.block_service import is_blocked
    if is_blocked(db, actor.id, target.id):
        raise HTTPException(403, "Không thể kết bạn do quan hệ chặn.")
    if actor.id == target.id:
        raise HTTPException(400, "Không thể thực hiện thao tác kết bạn với chính mình.")
    low, high = _pair(actor.id, target.id)
    friendship = db.get(Friendship, (low, high))
    request = _pending(db, actor.id, target.id)
    now = datetime.now(timezone.utc)
    if action == "add":
        if friendship:
            return "friends"
        if request:
            raise HTTPException(409, "Giữa hai tài khoản đã có lời mời đang chờ xử lý.")
        request = FriendRequest(sender_id=actor.id, receiver_id=target.id)
        db.add(request)
        db.flush()
        db.execute(text("INSERT INTO notifications (user_id,type,title,content,actor_id,reference_type,reference_id) VALUES (:uid,'FRIEND_REQUEST','Lời mời kết bạn',:content,:actor,'FRIEND_REQUEST',:ref)"), {"uid": target.id, "content": f"{actor.profile.full_name if actor.profile else actor.username} đã gửi lời mời kết bạn.", "actor": actor.id, "ref": request.id})
    elif action in {"accept", "reject"}:
        if not request or request.receiver_id != actor.id:
            raise HTTPException(404, "Không tìm thấy lời mời kết bạn gửi đến bạn.")
        request.status = FriendRequestStatus.ACCEPTED if action == "accept" else FriendRequestStatus.REJECTED
        request.responded_at = now
        if action == "accept":
            db.add(Friendship(user_low_id=low, user_high_id=high))
            db.execute(text("INSERT INTO notifications (user_id,type,title,content,actor_id,reference_type,reference_id) VALUES (:uid,'FRIEND_REQUEST','Lời mời được chấp nhận',:content,:actor,'USER',:ref)"), {"uid": target.id, "content": f"{actor.profile.full_name if actor.profile else actor.username} đã chấp nhận lời mời kết bạn.", "actor": actor.id, "ref": actor.id})
    elif action == "cancel":
        if not request or request.sender_id != actor.id:
            raise HTTPException(404, "Không tìm thấy lời mời do bạn gửi.")
        request.status, request.responded_at = FriendRequestStatus.CANCELLED, now
    elif action == "unfriend":
        if not friendship:
            return "none"
        db.delete(friendship)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Trạng thái kết bạn vừa được thay đổi. Hãy tải lại trang.") from exc
    return relation_status(db, actor.id, target.id)


def list_friends(db: Session, owner: User, viewer: User, query: str = "") -> list[FriendResponse]:
    friend_ids = list(db.scalars(text("SELECT CASE WHEN user_low_id=:uid THEN user_high_id ELSE user_low_id END FROM friendships WHERE user_low_id=:uid OR user_high_id=:uid ORDER BY created_at DESC").bindparams(uid=owner.id)).all())
    if not friend_ids:
        return []
    blocked_ids = select(text("CASE WHEN blocker_id=:viewer THEN blocked_id ELSE blocker_id END")).select_from(text("user_blocks")).where(text("blocker_id=:viewer OR blocked_id=:viewer")).params(viewer=viewer.id)
    statement = select(User).where(User.id.in_(friend_ids), User.id.not_in(blocked_ids), User.deleted_at.is_(None))
    if query.strip():
        value = f"%{query.strip()}%"
        statement = statement.join(User.profile).where(or_(User.username.ilike(value), text("profiles.full_name ILIKE :value").bindparams(value=value)))
    users = list(db.scalars(statement).unique().all())
    result = []
    for user in users:
        mutual = db.scalar(text("SELECT count(*) FROM (SELECT CASE WHEN user_low_id=:viewer THEN user_high_id ELSE user_low_id END id FROM friendships WHERE user_low_id=:viewer OR user_high_id=:viewer INTERSECT SELECT CASE WHEN user_low_id=:target THEN user_high_id ELSE user_low_id END id FROM friendships WHERE user_low_id=:target OR user_high_id=:target) m").bindparams(viewer=viewer.id, target=user.id)) or 0
        result.append(FriendResponse(id=str(user.id), name=user.profile.full_name if user.profile else user.username, username=user.username, avatar=_media_url(db, user.profile.avatar_media_id if user.profile else None, "/assets/logo.png"), mutualCount=mutual, faculty=user.profile.faculty if user.profile else None))
    return result
