import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from src.db.models.media import MediaFile, MediaStatus
from src.db.models.post import Comment, Post, PostLike, PostMedia, PostStatus, PostType, PostVisibility
from src.db.models.user import User
from src.models.group import GroupMemberResponse, GroupPostCreateRequest, GroupResponse, JoinRequestResponse, ModerationRequest
from src.services.post_service import _serialize


def _group(db: Session, group_id: uuid.UUID):
    row = db.execute(text("SELECT id,name,slug,description,status FROM groups WHERE id=:id"), {"id": group_id}).mappings().first()
    if not row or row["status"] != "ACTIVE":
        raise HTTPException(404, "Không tìm thấy nhóm.")
    return row


def _membership(db: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> str:
    role = db.execute(text("SELECT role FROM group_members WHERE group_id=:gid AND user_id=:uid"), {"gid": group_id, "uid": user_id}).scalar_one_or_none()
    if role:
        return str(role)
    pending = db.execute(text("SELECT 1 FROM group_join_requests WHERE group_id=:gid AND user_id=:uid AND status='PENDING'"), {"gid": group_id, "uid": user_id}).first()
    return "PENDING" if pending else "NONE"


def list_groups(db: Session, user: User) -> list[GroupResponse]:
    rows = db.execute(text("SELECT g.id,g.name,g.slug,g.description,count(gm.user_id) member_count FROM groups g LEFT JOIN group_members gm ON gm.group_id=g.id WHERE g.status='ACTIVE' GROUP BY g.id ORDER BY g.name")).mappings()
    return [
        GroupResponse(
            id=str(row["id"]),
            name=row["name"],
            slug=row["slug"],
            description=row["description"] or "",
            member_count=row["member_count"],
            membership=_membership(db, row["id"], user.id),
        )
        for row in rows
    ]


def request_join(db: Session, group_id: uuid.UUID, user: User) -> str:
    _group(db, group_id)
    if _membership(db, group_id, user.id) in {"MEMBER", "ADMIN"}:
        raise HTTPException(409, "Bạn đã là thành viên của nhóm.")
    db.execute(text("INSERT INTO group_join_requests(group_id,user_id,status) VALUES(:gid,:uid,'PENDING') ON CONFLICT(group_id,user_id) DO UPDATE SET status='PENDING',reviewed_by=NULL,reviewed_at=NULL,created_at=now()"), {"gid": group_id, "uid": user.id})
    db.commit()
    return "PENDING"


def leave(db: Session, group_id: uuid.UUID, user: User) -> None:
    role = _membership(db, group_id, user.id)
    if role == "ADMIN":
        raise HTTPException(409, "Super Admin phải thu hồi quyền trước khi admin rời nhóm.")
    result = db.execute(text("DELETE FROM group_members WHERE group_id=:gid AND user_id=:uid"), {"gid": group_id, "uid": user.id})
    if not result.rowcount:
        raise HTTPException(404, "Bạn chưa tham gia nhóm.")
    db.commit()


def create_post(db: Session, group_id: uuid.UUID, user: User, payload: GroupPostCreateRequest):
    from src.services.system_service import enforce_content
    enforce_content(db,payload.content,allow_review=True)
    _group(db, group_id)
    if _membership(db, group_id, user.id) not in {"MEMBER", "ADMIN"}:
        raise HTTPException(403, "Bạn phải là thành viên của nhóm để đăng bài.")
    media = list(db.scalars(select(MediaFile).where(MediaFile.id.in_(payload.media_ids))).all()) if payload.media_ids else []
    if len(media) != len(set(payload.media_ids)) or any(item.owner_id != user.id or item.status != MediaStatus.READY for item in media):
        raise HTTPException(400, "Media không hợp lệ hoặc không thuộc tài khoản này.")
    post = Post(group_id=group_id, author_id=user.id, content=payload.content.strip(), post_type=PostType.STANDARD, visibility=PostVisibility.PUBLIC, status=PostStatus.PENDING)
    db.add(post); db.flush()
    for index, media_id in enumerate(payload.media_ids):
        db.add(PostMedia(post_id=post.id, media_id=media_id, sort_order=index))
    db.commit(); db.refresh(post)
    return _serialize(db, post, user.id)


def list_posts(db: Session, group_id: uuid.UUID, user: User, *, pending: bool = False, query: str = "", sort: str = "latest"):
    _group(db, group_id)
    status = PostStatus.PENDING if pending else PostStatus.APPROVED
    statement = select(Post).where(Post.group_id == group_id, Post.status == status, Post.deleted_at.is_(None))
    if query.strip():
        statement = statement.where(Post.content.ilike(f"%{query.strip()}%"))
    if sort == "featured":
        likes = select(func.count()).select_from(PostLike).where(PostLike.post_id == Post.id).scalar_subquery()
        comments = select(func.count()).select_from(Comment).where(Comment.post_id == Post.id, Comment.deleted_at.is_(None)).scalar_subquery()
        statement = statement.order_by(Post.is_pinned.desc(), likes.desc(), comments.desc(), Post.created_at.desc())
    elif sort == "pinned":
        statement = statement.where(Post.is_pinned.is_(True)).order_by(Post.created_at.desc())
    else:
        statement = statement.order_by(Post.is_pinned.desc(), Post.created_at.desc())
    rows = db.scalars(statement).all()
    return [_serialize(db, item, user.id) for item in rows]


def list_my_posts(db: Session, group_id: uuid.UUID, user: User):
    _group(db, group_id)
    rows = db.scalars(select(Post).where(
        Post.group_id == group_id, Post.author_id == user.id, Post.deleted_at.is_(None)
    ).order_by(Post.created_at.desc())).all()
    return [_serialize(db, item, user.id) for item in rows]


def join_requests(db: Session, group_id: uuid.UUID) -> list[JoinRequestResponse]:
    _group(db, group_id)
    rows = db.execute(text("SELECT r.id,r.user_id,p.full_name name,u.username,r.created_at FROM group_join_requests r JOIN users u ON u.id=r.user_id JOIN profiles p ON p.user_id=u.id WHERE r.group_id=:gid AND r.status='PENDING' ORDER BY r.created_at"), {"gid": group_id}).mappings()
    return [JoinRequestResponse(id=str(r["id"]), user_id=str(r["user_id"]), name=r["name"], username=r["username"], created_at=r["created_at"].isoformat()) for r in rows]


def decide_join(db: Session, group_id: uuid.UUID, request_id: uuid.UUID, admin: User, approve: bool) -> None:
    row = db.execute(text("SELECT user_id FROM group_join_requests WHERE id=:id AND group_id=:gid AND status='PENDING' FOR UPDATE"), {"id": request_id, "gid": group_id}).first()
    if not row:
        raise HTTPException(404, "Không tìm thấy yêu cầu đang chờ.")
    decision = "APPROVED" if approve else "REJECTED"
    db.execute(text("UPDATE group_join_requests SET status=:status,reviewed_by=:admin,reviewed_at=now() WHERE id=:id"), {"status": decision, "admin": admin.id, "id": request_id})
    if approve:
        db.execute(text("INSERT INTO group_members(group_id,user_id,role) VALUES(:gid,:uid,'MEMBER') ON CONFLICT DO NOTHING"), {"gid": group_id, "uid": row.user_id})
    db.execute(text("INSERT INTO notifications(user_id,type,title,content,actor_id,reference_type,reference_id) VALUES(:uid,'SYSTEM','Kết quả yêu cầu tham gia nhóm',:content,:actor,'GROUP',:gid)"),{"uid":row.user_id,"content":"Yêu cầu tham gia nhóm đã được chấp nhận." if approve else "Yêu cầu tham gia nhóm đã bị từ chối.","actor":admin.id,"gid":group_id})
    db.commit()


def moderate_post(db: Session, group_id: uuid.UUID, post_id: uuid.UUID, admin: User, payload: ModerationRequest):
    post = db.get(Post, post_id)
    if not post or post.group_id != group_id or post.deleted_at is not None or post.status != PostStatus.PENDING:
        raise HTTPException(404, "Không tìm thấy bài viết đang chờ duyệt.")
    if payload.decision == "REJECT" and not (payload.reason or "").strip():
        raise HTTPException(400, "Phải nhập lý do khi từ chối bài viết.")
    post.status = PostStatus.APPROVED if payload.decision == "APPROVE" else PostStatus.REJECTED
    post.rejection_reason = None if payload.decision == "APPROVE" else payload.reason.strip()
    post.reviewed_by, post.reviewed_at = admin.id, datetime.now(UTC)
    db.execute(text("INSERT INTO notifications(user_id,type,title,content,actor_id,reference_type,reference_id) VALUES(:uid,'POST_REVIEW',:title,:content,:actor,'POST',:ref)"), {"uid": post.author_id, "title": "Kết quả kiểm duyệt bài viết", "content": "Bài viết đã được phê duyệt." if payload.decision == "APPROVE" else f"Bài viết bị từ chối: {payload.reason.strip()}", "actor": admin.id, "ref": post.id})
    db.commit(); db.refresh(post)
    return _serialize(db, post, admin.id)


def pin_post(db: Session, group_id: uuid.UUID, post_id: uuid.UUID, value: bool) -> None:
    post = db.get(Post, post_id)
    if not post or post.group_id != group_id or post.deleted_at is not None or post.status != PostStatus.APPROVED:
        raise HTTPException(404, "Không tìm thấy bài viết đã duyệt trong nhóm.")
    post.is_pinned = value; db.commit()


def members(db: Session, group_id: uuid.UUID, query: str = "") -> list[GroupMemberResponse]:
    pattern=f"%{query.strip()}%"
    rows = db.execute(text("SELECT u.id,p.full_name name,u.username,p.student_code,gm.role FROM group_members gm JOIN users u ON u.id=gm.user_id JOIN profiles p ON p.user_id=u.id WHERE gm.group_id=:gid AND (:q='' OR p.full_name ILIKE :pattern OR p.student_code ILIKE :pattern OR u.username ILIKE :pattern) ORDER BY gm.role,u.username"), {"gid": group_id,"q":query.strip(),"pattern":pattern}).mappings()
    return [GroupMemberResponse(id=str(r["id"]), name=r["name"], username=r["username"], student_code=r["student_code"], role=str(r["role"])) for r in rows]


def kick_member(db: Session, group_id: uuid.UUID, user_id: uuid.UUID, admin: User) -> None:
    result = db.execute(text("DELETE FROM group_members WHERE group_id=:gid AND user_id=:uid AND role='MEMBER'"), {"gid": group_id, "uid": user_id})
    if not result.rowcount:
        raise HTTPException(404, "Không tìm thấy thành viên hoặc không thể xóa quản trị viên.")
    db.execute(text("INSERT INTO notifications(user_id,type,title,content,actor_id,reference_type,reference_id) VALUES(:uid,'SYSTEM','Đã rời khỏi nhóm','Bạn đã được Group Admin mời khỏi nhóm.',:actor,'GROUP',:gid)"),{"uid":user_id,"actor":admin.id,"gid":group_id})
    db.commit()


def remove_approved_post(db: Session, group_id: uuid.UUID, post_id: uuid.UUID, admin: User, reason: str) -> None:
    post=db.get(Post,post_id)
    if not post or post.group_id!=group_id or post.deleted_at is not None or post.status!=PostStatus.APPROVED:
        raise HTTPException(404,"Không tìm thấy bài viết đã duyệt trong nhóm.")
    post.status=PostStatus.DELETED;post.deleted_at=datetime.now(UTC);post.rejection_reason=reason.strip()
    db.execute(text("INSERT INTO notifications(user_id,type,title,content,actor_id,reference_type,reference_id) VALUES(:uid,'POST_REVIEW','Bài viết đã bị gỡ',:content,:actor,'POST',:ref)"),{"uid":post.author_id,"content":f"Group Admin đã gỡ bài viết: {reason.strip()}","actor":admin.id,"ref":post.id})
    db.commit()


def delete_comment(db: Session, group_id: uuid.UUID, comment_id: uuid.UUID, admin: User) -> None:
    comment = db.get(Comment, comment_id)
    post = db.get(Post, comment.post_id) if comment else None
    if not comment or not post or post.group_id != group_id or comment.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy bình luận trong nhóm.")
    comment.deleted_at = datetime.now(UTC)
    db.execute(text("INSERT INTO notifications(user_id,type,title,content,actor_id,reference_type,reference_id) VALUES(:uid,'SYSTEM','Bình luận đã bị xóa','Group Admin đã xóa bình luận vi phạm trong nhóm.',:actor,'COMMENT',:ref)"),{"uid":comment.user_id,"actor":admin.id,"ref":comment.id})
    db.commit()
