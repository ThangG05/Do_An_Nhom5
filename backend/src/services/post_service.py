import base64
import json
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import and_, bindparam, func, or_, select, text
from sqlalchemy.orm import Session

from src.db.models.media import MediaFile, MediaStatus
from src.db.models.post import Comment, Post, PostLike, PostMedia, PostStatus, PostType, PostVisibility
from src.db.models.user import Profile, User
from src.models.post import CommentAuthorResponse, CommentCreateRequest, CommentResponse, CommentUpdateRequest, CreateProfilePostRequest, EventListingData, MarketListingData, PostAuthorResponse, PostLocationData, PostMediaResponse, ProfilePostResponse, RoomListingData, UpdatePostRequest
from src.models.user import UserListingResponse, UserPhotoResponse
from src.services.storage_service import create_download_url


def _are_friends(db: Session, first: uuid.UUID, second: uuid.UUID) -> bool:
    low, high = sorted((first, second))
    from sqlalchemy import text
    return bool(db.scalar(text("SELECT EXISTS(SELECT 1 FROM friendships WHERE user_low_id=:low AND user_high_id=:high)").bindparams(low=low, high=high)))


def _can_view(db: Session, post: Post, viewer_id: uuid.UUID) -> bool:
    return post.author_id == viewer_id or post.visibility == PostVisibility.PUBLIC or (post.visibility == PostVisibility.FRIENDS and _are_friends(db, post.author_id, viewer_id))


def _comment_response(db: Session, comment: Comment) -> CommentResponse:
    user = db.get(User, comment.user_id)
    avatar = "/assets/logo.png"
    if user and user.profile and user.profile.avatar_media_id:
        media = db.get(MediaFile, user.profile.avatar_media_id)
        if media and media.status == MediaStatus.READY:
            avatar = create_download_url(media)
    image_url = None
    if comment.media_id:
        attached = db.get(MediaFile, comment.media_id)
        if attached and attached.status == MediaStatus.READY:
            image_url = create_download_url(attached)
    return CommentResponse(id=str(comment.id), author=CommentAuthorResponse(id=str(user.id), name=user.profile.full_name if user.profile else user.username, avatar=avatar), content=comment.content, createdAt=comment.created_at.isoformat(), parentId=str(comment.parent_id) if comment.parent_id else None, imageUrl=image_url)


def _listing_data(payload: CreateProfilePostRequest | UpdatePostRequest, category: str) -> dict | None:
    value = {
        "market": payload.marketListing,
        "roommate": payload.roomListing,
        "event": payload.eventListing,
    }.get(category)
    return value.model_dump() if value is not None else None


def _serialize(db: Session, post: Post, viewer_id: uuid.UUID) -> ProfilePostResponse:
    author = db.get(User, post.author_id)
    avatar = "/assets/logo.png"
    if author and author.profile and author.profile.avatar_media_id:
        avatar_media = db.get(MediaFile, author.profile.avatar_media_id)
        if avatar_media and avatar_media.status == MediaStatus.READY:
            avatar = create_download_url(avatar_media)
    links = db.scalars(select(PostMedia).where(PostMedia.post_id == post.id).order_by(PostMedia.sort_order)).all()
    media_items = []
    for link in links:
        media = db.get(MediaFile, link.media_id)
        if media and media.status == MediaStatus.READY:
            kind = "image" if media.mime_type.startswith("image/") else "video" if media.mime_type.startswith("video/") else "audio" if media.mime_type.startswith("audio/") else "file"
            media_items.append(PostMediaResponse(id=str(media.id), url=create_download_url(media), type=kind, name=media.original_name, size=media.file_size))
    likes = db.scalar(select(func.count()).select_from(PostLike).where(PostLike.post_id == post.id)) or 0
    comment_rows = list(db.scalars(select(Comment).where(Comment.post_id == post.id, Comment.deleted_at.is_(None)).order_by(Comment.created_at)).all())
    liked = db.get(PostLike, (post.id, viewer_id)) is not None
    listing = post.listing_data or {}
    group = db.execute(text("SELECT name,slug FROM groups WHERE id=:gid"), {"gid": post.group_id}).mappings().first() if post.group_id else None
    return ProfilePostResponse(id=str(post.id), author=PostAuthorResponse(id=str(author.id), name=author.profile.full_name if author.profile else author.username, avatar=avatar), createdAt=post.created_at.isoformat(), content=post.content, category=post.category, privacy=post.visibility.value.lower(), media=media_items, likesCount=likes, commentsCount=len(comment_rows), isLiked=liked, comments=[_comment_response(db, item) for item in comment_rows], groupId=str(post.group_id) if post.group_id else None, groupName=group["name"] if group else None, groupSlug=group["slug"] if group else None, status=post.status.value, rejectionReason=post.rejection_reason, isPinned=post.is_pinned, marketListing=MarketListingData(**listing) if post.category == "market" and listing else None, roomListing=RoomListingData(**listing) if post.category == "roommate" and listing else None, eventListing=EventListingData(**listing) if post.category == "event" and listing else None, location=PostLocationData(**post.location_data) if post.location_data else None)


def _media_kind(mime_type: str) -> str:
    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("video/"):
        return "video"
    if mime_type.startswith("audio/"):
        return "audio"
    return "file"


def _serialize_feed_posts(db: Session, posts: list[Post], viewer_id: uuid.UUID) -> list[ProfilePostResponse]:
    """Serialize one feed page with batched queries instead of N+1 queries."""
    if not posts:
        return []
    post_ids = [post.id for post in posts]
    author_ids = {post.author_id for post in posts}
    authors = {user.id: user for user in db.scalars(select(User).where(User.id.in_(author_ids))).all()}
    profiles = {profile.user_id: profile for profile in db.scalars(select(Profile).where(Profile.user_id.in_(author_ids))).all()}
    avatar_ids = {profile.avatar_media_id for profile in profiles.values() if profile.avatar_media_id}

    links = db.scalars(select(PostMedia).where(PostMedia.post_id.in_(post_ids)).order_by(PostMedia.post_id, PostMedia.sort_order)).all()
    media_ids = avatar_ids | {link.media_id for link in links}
    media_by_id = {media.id: media for media in db.scalars(select(MediaFile).where(MediaFile.id.in_(media_ids), MediaFile.status == MediaStatus.READY)).all()} if media_ids else {}
    media_by_post: dict[uuid.UUID, list[MediaFile]] = {post_id: [] for post_id in post_ids}
    for link in links:
        if media := media_by_id.get(link.media_id):
            media_by_post[link.post_id].append(media)

    like_counts = dict(db.execute(select(PostLike.post_id, func.count()).where(PostLike.post_id.in_(post_ids)).group_by(PostLike.post_id)).all())
    comment_counts = dict(db.execute(select(Comment.post_id, func.count()).where(Comment.post_id.in_(post_ids), Comment.deleted_at.is_(None)).group_by(Comment.post_id)).all())
    liked_post_ids = set(db.scalars(select(PostLike.post_id).where(PostLike.post_id.in_(post_ids), PostLike.user_id == viewer_id)).all())

    # A home card only needs a preview. Windowing keeps one popular post from
    # loading thousands of comments during a feed request.
    ranked_comments = select(Comment.id.label("comment_id"), func.row_number().over(partition_by=Comment.post_id, order_by=Comment.created_at.desc()).label("rank")).where(Comment.post_id.in_(post_ids), Comment.deleted_at.is_(None)).subquery()
    preview_comments = db.scalars(select(Comment).join(ranked_comments, Comment.id == ranked_comments.c.comment_id).where(ranked_comments.c.rank <= 3).order_by(Comment.post_id, Comment.created_at)).all()
    comment_user_ids = {comment.user_id for comment in preview_comments}
    comment_users = {user.id: user for user in db.scalars(select(User).where(User.id.in_(comment_user_ids))).all()} if comment_user_ids else {}
    comment_profiles = {profile.user_id: profile for profile in db.scalars(select(Profile).where(Profile.user_id.in_(comment_user_ids))).all()} if comment_user_ids else {}
    comment_avatar_ids = {profile.avatar_media_id for profile in comment_profiles.values() if profile.avatar_media_id}
    comment_media_ids = {comment.media_id for comment in preview_comments if comment.media_id}
    extra_media_ids = (comment_avatar_ids | comment_media_ids) - set(media_by_id)
    if extra_media_ids:
        media_by_id.update({media.id: media for media in db.scalars(select(MediaFile).where(MediaFile.id.in_(extra_media_ids), MediaFile.status == MediaStatus.READY)).all()})
    comments_by_post: dict[uuid.UUID, list[CommentResponse]] = {post_id: [] for post_id in post_ids}
    for comment in preview_comments:
        user = comment_users.get(comment.user_id)
        if not user:
            continue
        profile = comment_profiles.get(user.id)
        avatar_media = media_by_id.get(profile.avatar_media_id) if profile and profile.avatar_media_id else None
        attached = media_by_id.get(comment.media_id) if comment.media_id else None
        comments_by_post[comment.post_id].append(CommentResponse(id=str(comment.id), author=CommentAuthorResponse(id=str(user.id), name=profile.full_name if profile else user.username, avatar=create_download_url(avatar_media) if avatar_media else "/assets/logo.png"), content=comment.content, createdAt=comment.created_at.isoformat(), parentId=str(comment.parent_id) if comment.parent_id else None, imageUrl=create_download_url(attached) if attached else None))

    group_ids = {post.group_id for post in posts if post.group_id}
    group_query = text("SELECT id,name,slug FROM groups WHERE id IN :group_ids").bindparams(bindparam("group_ids", expanding=True))
    groups = {row["id"]: row for row in db.execute(group_query, {"group_ids": list(group_ids)}).mappings().all()} if group_ids else {}
    result: list[ProfilePostResponse] = []
    for post in posts:
        author = authors[post.author_id]
        profile = profiles.get(author.id)
        avatar_media = media_by_id.get(profile.avatar_media_id) if profile and profile.avatar_media_id else None
        listing, group = post.listing_data or {}, groups.get(post.group_id)
        result.append(ProfilePostResponse(id=str(post.id), author=PostAuthorResponse(id=str(author.id), name=profile.full_name if profile else author.username, avatar=create_download_url(avatar_media) if avatar_media else "/assets/logo.png"), createdAt=post.created_at.isoformat(), content=post.content, category=post.category, privacy=post.visibility.value.lower(), media=[PostMediaResponse(id=str(media.id), url=create_download_url(media), type=_media_kind(media.mime_type), name=media.original_name, size=media.file_size) for media in media_by_post[post.id]], likesCount=like_counts.get(post.id, 0), commentsCount=comment_counts.get(post.id, 0), isLiked=post.id in liked_post_ids, comments=comments_by_post[post.id], groupId=str(post.group_id) if post.group_id else None, groupName=group["name"] if group else None, groupSlug=group["slug"] if group else None, status=post.status.value, rejectionReason=post.rejection_reason, isPinned=post.is_pinned, marketListing=MarketListingData(**listing) if post.category == "market" and listing else None, roomListing=RoomListingData(**listing) if post.category == "roommate" and listing else None, eventListing=EventListingData(**listing) if post.category == "event" and listing else None, location=PostLocationData(**post.location_data) if post.location_data else None))
    return result


def _decode_feed_cursor(cursor: str | None) -> tuple[datetime, uuid.UUID] | None:
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor.encode() + b"=" * (-len(cursor) % 4))
        data = json.loads(raw)
        return datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")), uuid.UUID(data["id"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(422, "Cursor bảng tin không hợp lệ.")


def _encode_feed_cursor(post: Post) -> str:
    raw = json.dumps({"created_at": post.created_at.isoformat(), "id": str(post.id)}, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def create_profile_post(db: Session, user: User, payload: CreateProfilePostRequest) -> ProfilePostResponse:
    from src.services.system_service import enforce_content
    if payload.content.strip():
        enforce_content(db,payload.content)
    media = list(db.scalars(select(MediaFile).where(MediaFile.id.in_(payload.media_ids))).all()) if payload.media_ids else []
    if len(media) != len(set(payload.media_ids)) or any(item.owner_id != user.id or item.status != MediaStatus.READY for item in media):
        raise HTTPException(400, "Có media không hợp lệ hoặc không thuộc tài khoản này.")
    post = Post(author_id=user.id, content=payload.content.strip(), category=payload.category, listing_data=_listing_data(payload, payload.category), location_data=payload.location.model_dump() if payload.location else None, post_type=PostType.PROFILE_POST, visibility=PostVisibility(payload.privacy.upper()), status=PostStatus.APPROVED)
    db.add(post)
    db.flush()
    for index, media_id in enumerate(payload.media_ids):
        db.add(PostMedia(post_id=post.id, media_id=media_id, sort_order=index))
    db.commit()
    db.refresh(post)
    return _serialize(db, post, user.id)


def list_profile_posts(db: Session, target: User, viewer: User) -> list[ProfilePostResponse]:
    allowed = [PostVisibility.PUBLIC]
    if target.id == viewer.id:
        allowed = list(PostVisibility)
    elif _are_friends(db, target.id, viewer.id):
        allowed.append(PostVisibility.FRIENDS)
    # Include approved group posts when the viewer can access that group.  The
    # former group_id IS NULL filter made a user's approved group posts vanish
    # from their own profile timeline.
    member_group_ids = select(text("group_id")).select_from(text("group_members")).where(text("user_id=:viewer_id")).params(viewer_id=viewer.id)
    group_visibility = or_(Post.group_id.is_(None), target.id == viewer.id, Post.group_id.in_(member_group_ids))
    posts = db.scalars(select(Post).where(Post.author_id == target.id, group_visibility, Post.status == PostStatus.APPROVED, Post.deleted_at.is_(None), Post.visibility.in_(allowed)).order_by(Post.created_at.desc())).all()
    return [_serialize(db, post, viewer.id) for post in posts]


def list_user_photos(db: Session, target: User, viewer: User) -> list[UserPhotoResponse]:
    photos: list[UserPhotoResponse] = []
    for post in list_profile_posts(db, target, viewer):
        album = "Ảnh đại diện" if post.category == "avatar" else "Ảnh tải lên"
        for media in post.media:
            if media.type == "image":
                photos.append(UserPhotoResponse(id=media.id, url=media.url, caption=post.content, createdAt=post.createdAt, likesCount=post.likesCount, albumName=album))
    return photos


def list_user_listings(db: Session, target: User, viewer: User, category: str | None = None) -> list[UserListingResponse]:
    result: list[UserListingResponse] = []
    for post in list_profile_posts(db, target, viewer):
        if post.category not in {"market", "roommate", "event"} or category and category != "all" and post.category != category:
            continue
        data = post.marketListing or post.roomListing or post.eventListing
        raw = data.model_dump() if data else {}
        price = raw.get("price") or raw.get("rentPerMonth") or ""
        title = next((line.strip() for line in post.content.splitlines() if line.strip()), "Bài đăng")
        result.append(UserListingResponse(id=post.id, title=title[:120], category=post.category, price=price, location=raw.get("location", ""), status=raw.get("status", "active"), imageUrl=next((item.url for item in post.media if item.type == "image"), ""), createdAt=post.createdAt, description=post.content))
    return result


def list_user_group_posts(db: Session, target: User, viewer: User) -> list[ProfilePostResponse]:
    """Return approved posts authored by a user inside groups, respecting membership visibility."""
    member_groups = select(text("group_id")).select_from(text("group_members")).where(text("user_id=:viewer_id")).params(viewer_id=viewer.id)
    posts = db.scalars(select(Post).where(
        Post.author_id == target.id,
        Post.group_id.is_not(None),
        or_(Post.author_id == viewer.id, Post.group_id.in_(member_groups)),
        Post.status == PostStatus.APPROVED,
        Post.deleted_at.is_(None),
    ).order_by(Post.created_at.desc())).all()
    return [_serialize(db, post, viewer.id) for post in posts]


def list_feed(db: Session, viewer: User, limit: int = 30, offset: int = 0, category: str | None = None, cursor: str | None = None) -> tuple[list[ProfilePostResponse], str | None]:
    friend_ids = select(text("CASE WHEN user_low_id=:uid THEN user_high_id ELSE user_low_id END")).select_from(text("friendships")).where(text("user_low_id=:uid OR user_high_id=:uid")).params(uid=viewer.id)
    visible = or_(Post.visibility == PostVisibility.PUBLIC, Post.author_id == viewer.id, and_(Post.visibility == PostVisibility.FRIENDS, Post.author_id.in_(friend_ids)))
    blocked_ids=select(text("CASE WHEN blocker_id=:uid THEN blocked_id ELSE blocker_id END")).select_from(text("user_blocks")).where(text("blocker_id=:uid OR blocked_id=:uid")).params(uid=viewer.id)
    # Home includes profile posts and approved posts from groups the viewer belongs to.
    # Pending/rejected posts and posts from unrelated groups must never leak into the feed.
    member_group_ids = select(text("group_id")).select_from(text("group_members")).where(text("user_id=:viewer_id")).params(viewer_id=viewer.id)
    group_scope = or_(Post.group_id.is_(None), Post.author_id == viewer.id, Post.group_id.in_(member_group_ids))
    filters=[group_scope,Post.author_id.not_in(blocked_ids),Post.status == PostStatus.APPROVED,Post.deleted_at.is_(None),visible]
    if category:
        filters.append(Post.category == category)
    # Cursor pagination stays on an index even for deep scrolling. `offset`
    # remains as a compatibility fallback for older frontend builds.
    cursor_values = _decode_feed_cursor(cursor)
    if cursor_values:
        created_at, post_id = cursor_values
        filters.append(or_(Post.created_at < created_at, and_(Post.created_at == created_at, Post.id < post_id)))
    query = select(Post).where(*filters).order_by(Post.created_at.desc(), Post.id.desc()).limit(limit + 1)
    if not cursor_values and offset:
        query = query.offset(offset)
    rows = list(db.scalars(query).all())
    has_next = len(rows) > limit
    posts = rows[:limit]
    return _serialize_feed_posts(db, posts, viewer.id), _encode_feed_cursor(posts[-1]) if has_next and posts else None


def get_visible_post(db: Session, post_id: uuid.UUID, viewer: User) -> Post:
    post = db.get(Post, post_id)
    if not post or post.deleted_at is not None or post.status != PostStatus.APPROVED:
        raise HTTPException(404, "Không tìm thấy bài viết.")
    if not _can_view(db, post, viewer.id):
        raise HTTPException(403, "Bạn không có quyền xem bài viết này.")
    return post


def get_post_response(db: Session, post_id: uuid.UUID, viewer: User) -> ProfilePostResponse:
    """Return one visible post for deep links from notifications."""
    return _serialize(db, get_visible_post(db, post_id, viewer), viewer.id)


def list_comments(db: Session, post_id: uuid.UUID, viewer: User, limit: int = 100) -> list[CommentResponse]:
    """Load a full comment thread only after the reader explicitly opens it."""
    get_visible_post(db, post_id, viewer)
    rows = db.scalars(
        select(Comment).where(Comment.post_id == post_id, Comment.deleted_at.is_(None)).order_by(Comment.created_at).limit(limit)
    ).all()
    return [_comment_response(db, comment) for comment in rows]


def set_like(db: Session, post_id: uuid.UUID, user: User, desired: bool) -> tuple[bool, int]:
    post = get_visible_post(db, post_id, user)
    like = db.get(PostLike, (post.id, user.id))
    if desired and not like:
        db.add(PostLike(post_id=post.id, user_id=user.id))
        _notify(db, post.author_id, user, "POST_LIKE", "Bài viết có lượt thích mới", "đã thích bài viết của bạn", post.id)
    elif not desired and like:
        db.delete(like)
    db.commit()
    count = db.scalar(select(func.count()).select_from(PostLike).where(PostLike.post_id == post.id)) or 0
    return desired, count


def _notify(db: Session, recipient_id: uuid.UUID, actor: User, kind: str, title: str, action: str, reference_id: uuid.UUID, payload: dict | None = None) -> None:
    if recipient_id == actor.id:
        return
    name = actor.profile.full_name if actor.profile else actor.username
    db.execute(text("INSERT INTO notifications (user_id,type,title,content,actor_id,reference_type,reference_id,payload) VALUES (:uid,CAST(:kind AS notification_type),:title,:content,:actor,'POST',:ref,CAST(:payload AS jsonb))"), {"uid": recipient_id, "kind": kind, "title": title, "content": f"{name} {action}.", "actor": actor.id, "ref": reference_id, "payload": json.dumps(payload or {})})


def add_comment(db: Session, post_id: uuid.UUID, user: User, payload: CommentCreateRequest) -> CommentResponse:
    from src.services.system_service import enforce_content
    enforce_content(db,payload.content)
    post = get_visible_post(db, post_id, user)
    if payload.parent_id:
        parent = db.get(Comment, payload.parent_id)
        if not parent or parent.post_id != post.id or parent.deleted_at is not None:
            raise HTTPException(400, "Bình luận cha không hợp lệ.")
    media = None
    if payload.media_id:
        media = db.get(MediaFile, payload.media_id)
        if not media or media.owner_id != user.id or media.status != MediaStatus.READY or not media.mime_type.startswith("image/"):
            raise HTTPException(400, "Ảnh bình luận không hợp lệ.")
    comment = Comment(post_id=post.id, user_id=user.id, parent_id=payload.parent_id, media_id=media.id if media else None, content=payload.content.strip())
    db.add(comment)
    db.flush()
    notification_payload = {"post_id": str(post.id), "comment_id": str(comment.id)}
    _notify(db, post.author_id, user, "COMMENT", "Bài viết có bình luận mới", "đã bình luận bài viết của bạn", post.id, notification_payload)
    if payload.parent_id and parent.user_id != post.author_id:
        _notify(db, parent.user_id, user, "COMMENT", "Bình luận của bạn có phản hồi mới", "đã trả lời bình luận của bạn", post.id, notification_payload)
    db.commit()
    db.refresh(comment)
    return _comment_response(db, comment)


def update_post(db: Session, post_id: uuid.UUID, user: User, payload: UpdatePostRequest) -> ProfilePostResponse:
    post = db.get(Post, post_id)
    if not post or post.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy bài viết.")
    if post.author_id != user.id:
        raise HTTPException(403, "Bạn chỉ có thể sửa bài viết của mình.")
    post.content = payload.content.strip()
    if payload.privacy:
        post.visibility = PostVisibility(payload.privacy.upper())
    previous_category = post.category
    if payload.category:
        post.category = payload.category
    listing_fields_supplied = any((payload.marketListing, payload.roomListing, payload.eventListing))
    if listing_fields_supplied or (payload.category and payload.category != previous_category):
        post.listing_data = _listing_data(payload, post.category)
    if payload.location is not None:
        post.location_data = payload.location.model_dump()
    if payload.media_ids is not None:
        media=list(db.scalars(select(MediaFile).where(MediaFile.id.in_(payload.media_ids))).all()) if payload.media_ids else []
        if len(media)!=len(set(payload.media_ids)) or any(item.owner_id!=user.id or item.status!=MediaStatus.READY for item in media):
            raise HTTPException(400,"Có media không hợp lệ hoặc không thuộc tài khoản này.")
        db.execute(text("DELETE FROM post_media WHERE post_id=:pid"),{"pid":post.id})
        for index,media_id in enumerate(payload.media_ids): db.add(PostMedia(post_id=post.id,media_id=media_id,sort_order=index))
    post.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(post)
    return _serialize(db, post, user.id)


def delete_post(db: Session, post_id: uuid.UUID, user: User) -> None:
    post = db.get(Post, post_id)
    if not post or post.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy bài viết.")
    if post.author_id != user.id:
        raise HTTPException(403, "Bạn chỉ có thể xóa bài viết của mình.")
    post.status, post.deleted_at = PostStatus.DELETED, datetime.now(timezone.utc)
    db.commit()

def update_comment(db:Session,comment_id:uuid.UUID,user:User,payload:CommentUpdateRequest)->CommentResponse:
    from src.services.system_service import enforce_content
    enforce_content(db,payload.content)
    comment=db.get(Comment,comment_id)
    if not comment or comment.deleted_at is not None: raise HTTPException(404,"Không tìm thấy bình luận.")
    if comment.user_id!=user.id: raise HTTPException(403,"Bạn chỉ có thể sửa bình luận của mình.")
    comment.content=payload.content.strip();comment.updated_at=datetime.now(timezone.utc);db.commit();db.refresh(comment)
    return _comment_response(db,comment)

def delete_comment(db:Session,comment_id:uuid.UUID,user:User)->None:
    comment=db.get(Comment,comment_id)
    if not comment or comment.deleted_at is not None: raise HTTPException(404,"Không tìm thấy bình luận.")
    if comment.user_id!=user.id: raise HTTPException(403,"Bạn chỉ có thể xóa bình luận của mình.")
    comment.deleted_at=datetime.now(timezone.utc);db.commit()
