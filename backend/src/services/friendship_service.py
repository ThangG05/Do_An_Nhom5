import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import bindparam, delete, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models.friendship import FriendRequest, FriendRequestStatus, Friendship
from src.db.models.media import MediaFile, MediaStatus
from src.db.models.user import Profile, User
from src.models.user import FriendResponse
from src.services.storage_service import create_download_url
from src.services.user_service import friendship_status


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
    friend_rows = db.execute(text("SELECT CASE WHEN user_low_id=:uid THEN user_high_id ELSE user_low_id END friend_id, created_at FROM friendships WHERE user_low_id=:uid OR user_high_id=:uid ORDER BY created_at DESC"), {"uid": owner.id}).mappings().all()
    friend_ids = [row["friend_id"] for row in friend_rows]
    if not friend_ids:
        return []
    blocked_ids = select(text("CASE WHEN blocker_id=:viewer THEN blocked_id ELSE blocker_id END")).select_from(text("user_blocks")).where(text("blocker_id=:viewer OR blocked_id=:viewer")).params(viewer=viewer.id)
    statement = select(User, Profile).outerjoin(Profile, Profile.user_id == User.id).where(
        User.id.in_(friend_ids), User.id.not_in(blocked_ids), User.deleted_at.is_(None)
    )
    if query.strip():
        value = f"%{query.strip()}%"
        statement = statement.where(or_(User.username.ilike(value), Profile.full_name.ilike(value)))
    user_rows = db.execute(statement).all()
    avatar_ids = {profile.avatar_media_id for _, profile in user_rows if profile and profile.avatar_media_id}
    avatars = {media.id: media for media in db.scalars(select(MediaFile).where(
        MediaFile.id.in_(avatar_ids), MediaFile.status == MediaStatus.READY
    )).all()} if avatar_ids else {}
    visible_ids = [user.id for user, _ in user_rows]
    mutual_query = text("""
        WITH viewer_friends AS (
            SELECT CASE WHEN user_low_id = :viewer THEN user_high_id ELSE user_low_id END AS id
            FROM friendships WHERE user_low_id = :viewer OR user_high_id = :viewer
        ), target_friends AS (
            SELECT user_low_id AS target_id, user_high_id AS mutual_id
            FROM friendships WHERE user_low_id IN :ids
            UNION ALL
            SELECT user_high_id AS target_id, user_low_id AS mutual_id
            FROM friendships WHERE user_high_id IN :ids
        )
        SELECT target_id, count(*) AS mutual_count
        FROM target_friends JOIN viewer_friends ON viewer_friends.id = target_friends.mutual_id
        GROUP BY target_id
    """).bindparams(bindparam("ids", expanding=True))
    mutual_counts = dict(db.execute(mutual_query, {"viewer": viewer.id, "ids": visible_ids}).all()) if visible_ids else {}
    viewer_friend_ids: set[uuid.UUID] = set()
    pending_by_id: dict[uuid.UUID, str] = {}
    if viewer.id != owner.id and visible_ids:
        friendship_rows = db.execute(text("""
            SELECT user_low_id, user_high_id FROM friendships
            WHERE (user_low_id=:viewer AND user_high_id IN :ids)
               OR (user_high_id=:viewer AND user_low_id IN :ids)
        """).bindparams(bindparam("ids", expanding=True)), {"viewer": viewer.id, "ids": visible_ids}).all()
        viewer_friend_ids = {high if low == viewer.id else low for low, high in friendship_rows}
        pending_rows = db.execute(text("""
            SELECT sender_id, receiver_id FROM friend_requests
            WHERE status='PENDING' AND
              ((sender_id=:viewer AND receiver_id IN :ids)
               OR (receiver_id=:viewer AND sender_id IN :ids))
        """).bindparams(bindparam("ids", expanding=True)), {"viewer": viewer.id, "ids": visible_ids}).all()
        pending_by_id = {
            receiver if sender == viewer.id else sender:
                "pending_sent" if sender == viewer.id else "pending_received"
            for sender, receiver in pending_rows
        }
    connected_at = {row["friend_id"]: row["created_at"] for row in friend_rows}
    result = []
    for user, profile in user_rows:
        avatar_media = avatars.get(profile.avatar_media_id) if profile and profile.avatar_media_id else None
        result.append(FriendResponse(
            id=str(user.id), name=profile.full_name if profile else user.username,
            username=user.username,
            avatar=create_download_url(avatar_media) if avatar_media else "/assets/logo.png",
            mutualCount=mutual_counts.get(user.id, 0),
            faculty=profile.faculty if profile else None,
            currentCity=profile.current_city if profile else None,
            hometown=profile.hometown if profile else None,
            connectedAt=connected_at[user.id].isoformat(),
            accountStatus=user.status.value,
            friendshipStatus=("self" if user.id == viewer.id else "friends" if viewer.id == owner.id or user.id in viewer_friend_ids else pending_by_id.get(user.id, "none")),
        ))
    return sorted(result, key=lambda friend: friend.connectedAt or "", reverse=True)
