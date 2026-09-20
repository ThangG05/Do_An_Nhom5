import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.dependencies import CurrentUser
from src.db.session import get_db
from src.db.models.user import User
from src.models.post import CreateProfilePostRequest, ProfilePostResponse
from src.models.user import BlockResponse, FriendResponse, FriendshipActionRequest, FriendshipActionResponse, ProfileResponse, ProfileUpdateRequest, UpdateAvatarRequest, UpdateAvatarResponse, UpdateCoverRequest, UpdateCoverResponse, UserListingResponse, UserPhotoResponse, UserSearchResponse
from src.services import block_service, friendship_service, post_service
from src.services.realtime_service import manager
from src.services.user_service import avatar_url, search_users, serialize_profile, update_avatar, update_cover, update_profile

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    return serialize_profile(db, current_user, current_user.id)


@router.patch("/me", response_model=ProfileResponse)
def patch_my_profile(payload: ProfileUpdateRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    return update_profile(db, current_user, payload)


@router.post("/me/posts", response_model=ProfilePostResponse, status_code=201)
def create_my_post(payload: CreateProfilePostRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    return post_service.create_profile_post(db, current_user, payload)


@router.put("/me/avatar", response_model=UpdateAvatarResponse)
def change_my_avatar(payload: UpdateAvatarRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    media, post = update_avatar(db, current_user, payload.media_id, payload.caption, payload.visibility, payload.create_post)
    return UpdateAvatarResponse(media_id=media.id, avatar_url=avatar_url(media), post_id=post.id if post else None)


@router.put("/me/cover", response_model=UpdateCoverResponse)
def change_my_cover(payload: UpdateCoverRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    media = update_cover(db, current_user, payload.media_id)
    return UpdateCoverResponse(media_id=media.id, cover_url=avatar_url(media))

@router.get("/me/blocked",response_model=list[FriendResponse])
def blocked_users(current_user:CurrentUser,db:Annotated[Session,Depends(get_db)]):
    ids=list(db.scalars(__import__('sqlalchemy').text("SELECT blocked_id FROM user_blocks WHERE blocker_id=:uid"),{"uid":current_user.id}))
    result=[]
    for uid in ids:
        user=db.get(User,uid)
        if user:result.append(FriendResponse(id=str(user.id),name=user.profile.full_name if user.profile else user.username,username=user.username,avatar="/assets/logo.png",mutualCount=0,faculty=user.profile.faculty if user.profile else None,friendshipStatus="blocked"))
    return result


@router.get("/search", response_model=list[UserSearchResponse])
def find_users(q: str, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)], limit: int = 20):
    return search_users(db, current_user, q, max(1, min(limit, 50)))


@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile(user_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    target = db.get(User, user_id)
    if target and block_service.is_blocked(db,current_user.id,target.id): raise HTTPException(403,"Không thể xem hồ sơ do quan hệ chặn.")
    if target is None or target.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy người dùng.")
    return serialize_profile(db, target, current_user.id)


@router.get("/{user_id}/posts", response_model=list[ProfilePostResponse])
def get_profile_posts(user_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    target = db.get(User, user_id)
    if target and block_service.is_blocked(db,current_user.id,target.id): raise HTTPException(403,"Không thể xem bài viết do quan hệ chặn.")
    if target is None or target.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy người dùng.")
    return post_service.list_profile_posts(db, target, current_user)


@router.get("/{user_id}/photos", response_model=list[UserPhotoResponse])
def get_profile_photos(user_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    target = db.get(User, user_id)
    if target is None or target.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy người dùng.")
    if block_service.is_blocked(db, current_user.id, target.id):
        raise HTTPException(403, "Không thể xem ảnh do quan hệ chặn.")
    return post_service.list_user_photos(db, target, current_user)


@router.get("/{user_id}/listings", response_model=list[UserListingResponse])
def get_profile_listings(user_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)], category: str = "all"):
    if category not in {"all", "market", "roommate", "event"}:
        raise HTTPException(422, "Loại listing không hợp lệ.")
    target = db.get(User, user_id)
    if target is None or target.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy người dùng.")
    if block_service.is_blocked(db, current_user.id, target.id):
        raise HTTPException(403, "Không thể xem listing do quan hệ chặn.")
    return post_service.list_user_listings(db, target, current_user, category)


@router.get("/{user_id}/friends", response_model=list[FriendResponse])
def get_friends(user_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)], q: str = ""):
    target = db.get(User, user_id)
    if target and block_service.is_blocked(db,current_user.id,target.id): raise HTTPException(403,"Không thể xem danh sách bạn bè do quan hệ chặn.")
    if target is None or target.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy người dùng.")
    return friendship_service.list_friends(db, target, current_user, q)


@router.post("/{user_id}/friendship", response_model=FriendshipActionResponse)
async def change_friendship(user_id: uuid.UUID, payload: FriendshipActionRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    target = db.get(User, user_id)
    if target is None or target.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy người dùng.")
    result=FriendshipActionResponse(status=friendship_service.act(db, current_user, target, payload.action))
    if payload.action in {"add","accept"}:await manager.send_users([target.id],{"event":"notification.created","type":"FRIEND_REQUEST"})
    return result

@router.put("/{user_id}/block",response_model=BlockResponse)
def block_user(user_id:uuid.UUID,current_user:CurrentUser,db:Annotated[Session,Depends(get_db)]):
    target=db.get(User,user_id)
    if not target or target.deleted_at is not None:raise HTTPException(404,"Không tìm thấy người dùng.")
    return BlockResponse(blocked=block_service.set_block(db,current_user,target,True))

@router.delete("/{user_id}/block",response_model=BlockResponse)
def unblock_user(user_id:uuid.UUID,current_user:CurrentUser,db:Annotated[Session,Depends(get_db)]):
    target=db.get(User,user_id)
    if not target:raise HTTPException(404,"Không tìm thấy người dùng.")
    return BlockResponse(blocked=block_service.set_block(db,current_user,target,False))
