import uuid
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from src.db.models.media import MediaFile, MediaStatus
from src.db.models.post import Post, PostMedia, PostStatus, PostType, PostVisibility
from src.db.models.user import Profile, User
from src.services.storage_service import create_download_url
from src.models.user import JoinedGroupResponse, ProfileResponse, ProfileUpdateRequest, UserSearchResponse


def _media_url(db: Session, media_id: uuid.UUID | None, fallback: str) -> str:
    if not media_id:
        return fallback
    media = db.get(MediaFile, media_id)
    return create_download_url(media) if media and media.status == MediaStatus.READY else fallback


def friendship_status(db: Session, viewer_id: uuid.UUID, target_id: uuid.UUID) -> str:
    if viewer_id == target_id:
        return "self"
    low, high = sorted((viewer_id, target_id))
    exists = db.execute(select(1).where(__import__('sqlalchemy').text("EXISTS (SELECT 1 FROM friendships WHERE user_low_id=:low AND user_high_id=:high)")).params(low=low, high=high)).scalar()
    if exists:
        return "friends"
    pending = db.execute(__import__('sqlalchemy').text("SELECT sender_id FROM friend_requests WHERE status='PENDING' AND ((sender_id=:viewer AND receiver_id=:target) OR (sender_id=:target AND receiver_id=:viewer)) LIMIT 1"), {"viewer": viewer_id, "target": target_id}).scalar()
    if pending is None:
        return "none"
    return "pending_sent" if pending == viewer_id else "pending_received"


def serialize_profile(db: Session, user: User, viewer_id: uuid.UUID) -> ProfileResponse:
    profile = user.profile
    if profile is None:
        raise HTTPException(404, "Không tìm thấy hồ sơ người dùng.")
    friends_count = db.scalar(select(func.count()).select_from(__import__('sqlalchemy').text("friendships")).where(or_(__import__('sqlalchemy').column("user_low_id") == user.id, __import__('sqlalchemy').column("user_high_id") == user.id))) or 0
    joined = db.execute(__import__('sqlalchemy').text("SELECT g.id,g.name,g.slug,gm.role FROM group_members gm JOIN groups g ON g.id=gm.group_id WHERE gm.user_id=:uid AND g.status='ACTIVE' ORDER BY g.name"), {"uid": user.id}).mappings().all()
    return ProfileResponse(
        id=str(user.id), name=profile.full_name, username=user.username,
        avatar=_media_url(db, profile.avatar_media_id, "/assets/logo.png"),
        coverBanner=_media_url(db, profile.cover_media_id, "/assets/logo.png"),
        bio=profile.bio or "", pronouns=profile.pronouns or "", studentCode=profile.student_code, faculty=profile.faculty,
        courseYear=profile.cohort, joinedDate=user.created_at.isoformat(), email=user.email,
        workplace=profile.workplace or "", education=profile.education or "Học viện Ngân hàng (BAV)",
        currentCity=profile.current_city or "", hometown=profile.hometown or "", socialLinks=profile.social_links or {},
        isVerified=user.email_verified_at is not None, friendsCount=friends_count,
        friendshipStatus=friendship_status(db, viewer_id, user.id),
        joinedGroups=[JoinedGroupResponse(id=str(row["id"]), name=row["name"], slug=row["slug"], role=str(row["role"])) for row in joined],
    )


def update_profile(db: Session, user: User, payload: ProfileUpdateRequest) -> ProfileResponse:
    profile = user.profile
    if profile is None:
        raise HTTPException(404, "Không tìm thấy hồ sơ người dùng.")
    changes = payload.model_dump(exclude_unset=True)
    mapping = {"courseYear": "cohort", "currentCity": "current_city", "socialLinks": "social_links"}
    for field, value in changes.items():
        setattr(profile, mapping.get(field, field), value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(profile)
    return serialize_profile(db, user, user.id)


def search_users(db: Session, viewer: User, query: str, limit: int = 20) -> list[UserSearchResponse]:
    term = query.strip()
    if len(term) < 2:
        return []
    pattern = f"%{term}%"
    rows = db.execute(
        __import__('sqlalchemy').text("""
            SELECT u.id, u.username, p.full_name, p.student_code, p.faculty,
                   p.avatar_media_id
            FROM users u
            JOIN profiles p ON p.user_id = u.id
            WHERE u.id <> :viewer
              AND u.deleted_at IS NULL
              AND u.status = 'ACTIVE'
              AND NOT EXISTS (
                SELECT 1 FROM user_blocks b
                WHERE (b.blocker_id = :viewer AND b.blocked_id = u.id)
                   OR (b.blocker_id = u.id AND b.blocked_id = :viewer)
              )
              AND (p.full_name ILIKE :pattern OR p.student_code ILIKE :pattern OR u.username ILIKE :pattern)
            ORDER BY
              CASE WHEN lower(coalesce(p.student_code, '')) = lower(:term) THEN 0
                   WHEN lower(u.username) = lower(:term) THEN 1
                   WHEN lower(p.full_name) = lower(:term) THEN 2 ELSE 3 END,
              p.full_name
            LIMIT :limit
        """),
        {"viewer": viewer.id, "pattern": pattern, "term": term, "limit": limit},
    ).mappings().all()
    result: list[UserSearchResponse] = []
    for row in rows:
        result.append(UserSearchResponse(
            id=str(row["id"]), name=row["full_name"], username=row["username"],
            avatar=_media_url(db, row["avatar_media_id"], "/assets/logo.png"),
            mutualCount=0, faculty=row["faculty"], studentCode=row["student_code"],
            friendshipStatus=friendship_status(db, viewer.id, row["id"]),
        ))
    return result


def update_avatar(db: Session, user: User, media_id: uuid.UUID, caption: str, visibility: str, create_post: bool) -> tuple[MediaFile, Post | None]:
    media = db.get(MediaFile, media_id)
    if media is None or media.owner_id != user.id or media.status != MediaStatus.READY or not media.mime_type.startswith("image/"):
        raise HTTPException(400, "Ảnh chưa được tải lên hoàn tất hoặc không thuộc tài khoản này.")
    profile = db.get(Profile, user.id)
    if profile is None:
        raise HTTPException(404, "Không tìm thấy hồ sơ người dùng.")
    profile.avatar_media_id = media.id
    post = None
    if create_post:
        post = Post(author_id=user.id, content=caption.strip(), post_type=PostType.PROFILE_AVATAR, visibility=PostVisibility(visibility), status=PostStatus.APPROVED)
        db.add(post)
        db.flush()
        db.add(PostMedia(post_id=post.id, media_id=media.id, sort_order=0))
    db.commit()
    return media, post


def avatar_url(media: MediaFile) -> str:
    return create_download_url(media)


def update_cover(db: Session, user: User, media_id: uuid.UUID) -> MediaFile:
    media = db.get(MediaFile, media_id)
    if media is None or media.owner_id != user.id or media.status != MediaStatus.READY or not media.mime_type.startswith("image/"):
        raise HTTPException(400, "Ảnh bìa chưa tải xong hoặc không thuộc tài khoản này.")
    if user.profile is None:
        raise HTTPException(404, "Không tìm thấy hồ sơ người dùng.")
    user.profile.cover_media_id = media.id
    db.commit()
    return media
