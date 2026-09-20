import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from src.api.dependencies import CurrentUser
from src.config import settings
from src.db.session import get_db
from src.models.media import CompleteUploadRequest, MediaResponse, PresignUploadRequest, PresignUploadResponse
from src.services.storage_service import complete_upload, create_avatar_upload, upload_avatar_from_backend, upload_post_media_from_backend

router = APIRouter(prefix="/media", tags=["Media"])

@router.post("/upload/avatar", response_model=MediaResponse)
async def upload_avatar(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)], file: Annotated[UploadFile, File()]):
    content = await file.read(settings.MAX_AVATAR_BYTES + 1)
    filename, content_type = file.filename or "avatar", file.content_type or ""
    await file.close()
    media = upload_avatar_from_backend(db, current_user.id, filename, content_type, content)
    return MediaResponse(media_id=media.id, status=media.status.value)


@router.post("/upload/cover", response_model=MediaResponse)
async def upload_cover(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)], file: Annotated[UploadFile, File()]):
    content = await file.read(settings.MAX_AVATAR_BYTES + 1)
    filename, content_type = file.filename or "cover", file.content_type or ""
    await file.close()
    media = upload_avatar_from_backend(db, current_user.id, filename, content_type, content, purpose="covers")
    return MediaResponse(media_id=media.id, status=media.status.value)


@router.post("/upload/post", response_model=MediaResponse)
async def upload_post_media(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)], file: Annotated[UploadFile, File()]):
    maximum = max(settings.MAX_SHORT_VIDEO_BYTES, settings.MAX_AUDIO_BYTES, settings.MAX_AVATAR_BYTES, settings.MAX_FILE_BYTES)
    content = await file.read(maximum + 1)
    filename, content_type = file.filename or "media", file.content_type or ""
    await file.close()
    media = upload_post_media_from_backend(db, current_user.id, filename, content_type, content)
    return MediaResponse(media_id=media.id, status=media.status.value)


@router.post("/upload/message", response_model=MediaResponse)
async def upload_message_media(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)], file: Annotated[UploadFile, File()]):
    maximum = max(settings.MAX_SHORT_VIDEO_BYTES, settings.MAX_AUDIO_BYTES, settings.MAX_AVATAR_BYTES, settings.MAX_FILE_BYTES)
    content = await file.read(maximum + 1)
    filename, content_type = file.filename or "media", file.content_type or ""
    await file.close()
    media = upload_post_media_from_backend(db, current_user.id, filename, content_type, content, purpose="messages")
    return MediaResponse(media_id=media.id, status=media.status.value)

@router.post("/upload/comment", response_model=MediaResponse)
async def upload_comment_image(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)], file: Annotated[UploadFile, File()]):
    content = await file.read(settings.MAX_AVATAR_BYTES + 1)
    filename, content_type = file.filename or "comment", file.content_type or ""
    await file.close()
    media = upload_avatar_from_backend(db, current_user.id, filename, content_type, content, purpose="comments")
    return MediaResponse(media_id=media.id, status=media.status.value)


@router.post("/presign", response_model=PresignUploadResponse)
def presign_upload(payload: PresignUploadRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    media, upload_url = create_avatar_upload(db, current_user.id, payload.original_name, payload.mime_type, payload.file_size)
    return PresignUploadResponse(media_id=media.id, upload_url=upload_url, expires_in=settings.R2_PRESIGNED_URL_EXPIRE, headers={"Content-Type": media.mime_type})

@router.post("/{media_id}/complete", response_model=MediaResponse)
def confirm_upload(media_id: uuid.UUID, payload: CompleteUploadRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]):
    media = complete_upload(db, current_user.id, media_id, payload.width, payload.height)
    return MediaResponse(media_id=media.id, status=media.status.value)
