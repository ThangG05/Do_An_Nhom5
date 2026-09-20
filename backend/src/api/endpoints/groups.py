import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from src.api.dependencies import CurrentGroupAdmin, CurrentUser
from src.db.session import get_db
from src.models.auth import MessageResponse
from src.models.group import GroupMemberResponse, GroupPostCreateRequest, GroupResponse, JoinRequestDecision, JoinRequestResponse, ModerationRequest, PinRequest, RemovePostRequest
from src.models.post import ProfilePostResponse
from src.services import group_service
from src.db.models.post import Comment, Post
from src.services.realtime_service import manager

router = APIRouter(prefix="/groups", tags=["Groups"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[GroupResponse])
def groups(current_user: CurrentUser, db: DbSession):
    return group_service.list_groups(db, current_user)


@router.post("/{group_id}/join", response_model=MessageResponse)
def join(group_id: uuid.UUID, current_user: CurrentUser, db: DbSession):
    group_service.request_join(db, group_id, current_user)
    return MessageResponse(message="Yêu cầu tham gia đang chờ Group Admin phê duyệt.")


@router.delete("/{group_id}/leave", status_code=204)
def leave(group_id: uuid.UUID, current_user: CurrentUser, db: DbSession):
    group_service.leave(db, group_id, current_user)
    return Response(status_code=204)


@router.get("/{group_id}/posts", response_model=list[ProfilePostResponse])
def posts(group_id: uuid.UUID, current_user: CurrentUser, db: DbSession, q: str = "", sort: Literal["latest", "featured", "pinned"] = "latest"):
    return group_service.list_posts(db, group_id, current_user, query=q, sort=sort)


@router.get("/{group_id}/posts/mine", response_model=list[ProfilePostResponse])
def my_posts(group_id: uuid.UUID, current_user: CurrentUser, db: DbSession):
    return group_service.list_my_posts(db, group_id, current_user)


@router.post("/{group_id}/posts", response_model=ProfilePostResponse, status_code=201)
def create_post(group_id: uuid.UUID, payload: GroupPostCreateRequest, current_user: CurrentUser, db: DbSession):
    return group_service.create_post(db, group_id, current_user, payload)


@router.get("/{group_id}/admin/join-requests", response_model=list[JoinRequestResponse])
def pending_members(group_id: uuid.UUID, admin: CurrentGroupAdmin, db: DbSession):
    return group_service.join_requests(db, group_id)


@router.patch("/{group_id}/admin/join-requests/{request_id}", status_code=204)
async def decide_member(group_id: uuid.UUID, request_id: uuid.UUID, payload: JoinRequestDecision, admin: CurrentGroupAdmin, db: DbSession):
    from sqlalchemy import text
    target_id=db.execute(text("SELECT user_id FROM group_join_requests WHERE id=:id AND group_id=:gid"),{"id":request_id,"gid":group_id}).scalar()
    group_service.decide_join(db, group_id, request_id, admin, payload.decision == "APPROVE")
    if target_id:await manager.send_users([target_id],{"event":"notification.created","type":"SYSTEM"})
    return Response(status_code=204)


@router.get("/{group_id}/admin/members", response_model=list[GroupMemberResponse])
def members(group_id: uuid.UUID, admin: CurrentGroupAdmin, db: DbSession, q: str = ""):
    return group_service.members(db, group_id, q)


@router.delete("/{group_id}/admin/members/{user_id}", status_code=204)
async def kick(group_id: uuid.UUID, user_id: uuid.UUID, admin: CurrentGroupAdmin, db: DbSession):
    group_service.kick_member(db, group_id, user_id, admin)
    await manager.send_users([user_id],{"event":"notification.created","type":"SYSTEM"})
    return Response(status_code=204)


@router.get("/{group_id}/admin/posts/pending", response_model=list[ProfilePostResponse])
def pending_posts(group_id: uuid.UUID, admin: CurrentGroupAdmin, db: DbSession):
    return group_service.list_posts(db, group_id, admin, pending=True)


@router.patch("/{group_id}/admin/posts/{post_id}/moderate", response_model=ProfilePostResponse)
async def moderate(group_id: uuid.UUID, post_id: uuid.UUID, payload: ModerationRequest, admin: CurrentGroupAdmin, db: DbSession):
    result=group_service.moderate_post(db, group_id, post_id, admin, payload)
    post=db.get(Post,post_id)
    if post:await manager.send_users([post.author_id],{"event":"notification.created","type":"POST_REVIEW"})
    return result


@router.put("/{group_id}/admin/posts/{post_id}/pin", status_code=204)
def pin(group_id: uuid.UUID, post_id: uuid.UUID, payload: PinRequest, admin: CurrentGroupAdmin, db: DbSession):
    group_service.pin_post(db, group_id, post_id, payload.is_pinned)
    return Response(status_code=204)


@router.delete("/{group_id}/admin/comments/{comment_id}", status_code=204)
async def remove_comment(group_id: uuid.UUID, comment_id: uuid.UUID, admin: CurrentGroupAdmin, db: DbSession):
    comment=db.get(Comment,comment_id);author_id=comment.user_id if comment else None
    group_service.delete_comment(db, group_id, comment_id, admin)
    if author_id:await manager.send_users([author_id],{"event":"notification.created","type":"SYSTEM"})
    return Response(status_code=204)


@router.delete("/{group_id}/admin/posts/{post_id}", status_code=204)
async def remove_approved_post(group_id: uuid.UUID, post_id: uuid.UUID, payload: RemovePostRequest, admin: CurrentGroupAdmin, db: DbSession):
    post=db.get(Post,post_id);author_id=post.author_id if post else None
    group_service.remove_approved_post(db,group_id,post_id,admin,payload.reason)
    if author_id:await manager.send_users([author_id],{"event":"notification.created","type":"POST_REVIEW"})
    return Response(status_code=204)
