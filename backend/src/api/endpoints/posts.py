import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from src.api.dependencies import CurrentUser
from src.db.session import get_db
from src.models.post import CommentCreateRequest, CommentResponse, CommentUpdateRequest, LikeRequest, LikeResponse, ProfilePostResponse, UpdatePostRequest
from src.services import post_service
from src.db.models.post import Post
from src.services.realtime_service import manager

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/feed", response_model=list[ProfilePostResponse])
def feed(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)], limit: Annotated[int, Query(ge=1, le=100)] = 30, offset: Annotated[int, Query(ge=0)] = 0, category: Annotated[str | None, Query(pattern="^(general|market|roommate|event|study)$")]=None):
    return post_service.list_feed(db, current_user, limit, offset, category)


@router.put("/{post_id}/like", response_model=LikeResponse)
async def like(post_id: uuid.UUID, payload: LikeRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    liked, count = post_service.set_like(db, post_id, current_user, payload.is_liked)
    post=db.get(Post,post_id)
    if payload.is_liked and post and post.author_id!=current_user.id: await manager.send_users([post.author_id],{"event":"notification.created","type":"POST_LIKE"})
    return LikeResponse(isLiked=liked, likesCount=count)


@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def comment(post_id: uuid.UUID, payload: CommentCreateRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    result=post_service.add_comment(db, post_id, current_user, payload)
    post=db.get(Post,post_id)
    recipients={post.author_id} if post and post.author_id!=current_user.id else set()
    if payload.parent_id:
        from src.db.models.post import Comment
        parent=db.get(Comment,payload.parent_id)
        if parent and parent.user_id!=current_user.id:recipients.add(parent.user_id)
    await manager.send_users(recipients,{"event":"notification.created","type":"COMMENT"})
    return result

@router.patch("/comments/{comment_id}",response_model=CommentResponse)
def edit_comment(comment_id:uuid.UUID,payload:CommentUpdateRequest,current_user:CurrentUser,db:Annotated[Session,Depends(get_db)]):return post_service.update_comment(db,comment_id,current_user,payload)

@router.delete("/comments/{comment_id}",status_code=204)
def remove_comment(comment_id:uuid.UUID,current_user:CurrentUser,db:Annotated[Session,Depends(get_db)]):post_service.delete_comment(db,comment_id,current_user);return Response(status_code=204)


@router.patch("/{post_id}", response_model=ProfilePostResponse)
def edit(post_id: uuid.UUID, payload: UpdatePostRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    return post_service.update_post(db, post_id, current_user, payload)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove(post_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    post_service.delete_post(db, post_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
