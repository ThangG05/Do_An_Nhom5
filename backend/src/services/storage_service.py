import io
import hashlib
import uuid
from enum import Enum
from datetime import datetime, timezone
from functools import lru_cache

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from src.config import settings
from src.db.models.media import MediaFile, MediaStatus

ALLOWED_IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
ALLOWED_SHORT_VIDEO_TYPES = {"video/mp4": "mp4", "video/webm": "webm", "video/quicktime": "mov"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg": "mp3", "audio/mp4": "m4a", "audio/ogg": "ogg", "audio/wav": "wav", "audio/webm": "webm"}
ALLOWED_FILE_TYPES = {
    "application/pdf": "pdf", "text/plain": "txt",
    "application/msword": "doc", "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.ms-excel": "xls", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-powerpoint": "ppt", "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/zip": "zip",
}
PIL_IMAGE_TYPES = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


class MediaKind(str, Enum):
    IMAGE = "images"
    SHORT_VIDEO = "short-videos"
    AUDIO = "audio"
    FILE = "files"


def build_object_key(kind: MediaKind, owner_id: uuid.UUID, purpose: str, media_id: uuid.UUID, extension: str) -> str:
    safe_purpose = purpose.strip().lower().replace("_", "-")
    if not safe_purpose or not safe_purpose.replace("-", "").isalnum():
        raise ValueError("Mục đích lưu media không hợp lệ.")
    return f"{kind.value}/users/{owner_id}/{safe_purpose}/{media_id}.{extension}"


def _require_r2_settings() -> None:
    missing = [name for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME") if not getattr(settings, name)]
    if missing:
        raise RuntimeError(f"Thiếu cấu hình R2: {', '.join(missing)}")


@lru_cache
def get_r2_client():
    _require_r2_settings()
    return boto3.client("s3", endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com", aws_access_key_id=settings.R2_ACCESS_KEY_ID, aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY, region_name="auto", config=Config(signature_version="s3v4"))


def check_r2_connection() -> dict[str, str]:
    try:
        get_r2_client().head_bucket(Bucket=settings.R2_BUCKET_NAME)
        return {"status": "ok", "bucket": settings.R2_BUCKET_NAME}
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError("Không thể kết nối hoặc không có quyền truy cập bucket R2.") from exc


def create_avatar_upload(db: Session, owner_id: uuid.UUID, original_name: str, mime_type: str, file_size: int) -> tuple[MediaFile, str]:
    extension = ALLOWED_IMAGE_TYPES.get(mime_type)
    if extension is None:
        raise HTTPException(400, "Chỉ hỗ trợ ảnh JPEG, PNG hoặc WEBP.")
    if file_size <= 0 or file_size > settings.MAX_AVATAR_BYTES:
        raise HTTPException(400, "Ảnh đại diện phải nhỏ hơn hoặc bằng 5MB.")
    media_id = uuid.uuid4()
    media = MediaFile(id=media_id, owner_id=owner_id, bucket=settings.R2_BUCKET_NAME, object_key=build_object_key(MediaKind.IMAGE, owner_id, "avatars", media_id, extension), original_name=original_name[:255], mime_type=mime_type, file_size=file_size, status=MediaStatus.PENDING)
    db.add(media)
    db.commit()
    db.refresh(media)
    upload_url = get_r2_client().generate_presigned_url("put_object", Params={"Bucket": media.bucket, "Key": media.object_key, "ContentType": media.mime_type}, ExpiresIn=settings.R2_PRESIGNED_URL_EXPIRE)
    return media, upload_url


def complete_upload(db: Session, owner_id: uuid.UUID, media_id: uuid.UUID, width: int | None, height: int | None) -> MediaFile:
    media = db.get(MediaFile, media_id)
    if media is None or media.owner_id != owner_id or media.deleted_at is not None:
        raise HTTPException(404, "Không tìm thấy tệp tải lên.")
    if media.status == MediaStatus.READY:
        return media
    if media.status != MediaStatus.PENDING:
        raise HTTPException(409, "Tệp không còn ở trạng thái chờ tải lên.")
    try:
        result = get_r2_client().head_object(Bucket=media.bucket, Key=media.object_key)
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(400, "Chưa tìm thấy ảnh trên R2. Hãy tải ảnh lên trước.") from exc
    if int(result.get("ContentLength", -1)) != media.file_size or str(result.get("ContentType", "")).split(";")[0].lower() != media.mime_type:
        media.status = MediaStatus.FAILED
        db.commit()
        raise HTTPException(400, "Kích thước hoặc định dạng ảnh trên R2 không khớp.")
    media.width, media.height = width, height
    media.status = MediaStatus.READY
    media.uploaded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(media)
    return media


def upload_avatar_from_backend(db: Session, owner_id: uuid.UUID, original_name: str, declared_type: str, content: bytes, purpose: str = "avatars") -> MediaFile:
    if not content or len(content) > settings.MAX_AVATAR_BYTES:
        raise HTTPException(400, "Ảnh đại diện phải nhỏ hơn hoặc bằng 5MB.")
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
        with Image.open(io.BytesIO(content)) as image:
            actual_type = PIL_IMAGE_TYPES.get(image.format or "")
            width, height = image.size
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(400, "Tệp tải lên không phải ảnh hợp lệ.") from exc
    if actual_type is None or declared_type != actual_type:
        raise HTTPException(400, "Định dạng thực tế của ảnh không khớp với tệp đã chọn.")
    media_id = uuid.uuid4()
    media = MediaFile(id=media_id, owner_id=owner_id, bucket=settings.R2_BUCKET_NAME, object_key=build_object_key(MediaKind.IMAGE, owner_id, purpose, media_id, ALLOWED_IMAGE_TYPES[actual_type]), original_name=original_name[:255], mime_type=actual_type, file_size=len(content), checksum_sha256=hashlib.sha256(content).hexdigest(), width=width, height=height, status=MediaStatus.PENDING)
    db.add(media)
    db.flush()
    try:
        get_r2_client().put_object(Bucket=media.bucket, Key=media.object_key, Body=content, ContentType=media.mime_type)
    except (BotoCoreError, ClientError) as exc:
        db.rollback()
        raise HTTPException(502, "Không thể tải ảnh lên Cloudflare R2.") from exc
    media.status = MediaStatus.READY
    media.uploaded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(media)
    return media


def upload_post_media_from_backend(db: Session, owner_id: uuid.UUID, original_name: str, mime_type: str, content: bytes, purpose: str = "posts") -> MediaFile:
    if mime_type in ALLOWED_IMAGE_TYPES:
        return upload_avatar_from_backend(db, owner_id, original_name, mime_type, content, purpose=purpose)
    if mime_type in ALLOWED_SHORT_VIDEO_TYPES:
        kind, extension, limit = MediaKind.SHORT_VIDEO, ALLOWED_SHORT_VIDEO_TYPES[mime_type], settings.MAX_SHORT_VIDEO_BYTES
    elif mime_type in ALLOWED_AUDIO_TYPES:
        kind, extension, limit = MediaKind.AUDIO, ALLOWED_AUDIO_TYPES[mime_type], settings.MAX_AUDIO_BYTES
    elif mime_type in ALLOWED_FILE_TYPES:
        kind, extension, limit = MediaKind.FILE, ALLOWED_FILE_TYPES[mime_type], settings.MAX_FILE_BYTES
    else:
        raise HTTPException(400, "Định dạng media không được hỗ trợ.")
    if not content or len(content) > limit:
        raise HTTPException(400, "Dung lượng media vượt quá giới hạn cho phép.")
    signatures_ok = mime_type in ALLOWED_FILE_TYPES and (
        (mime_type == "application/pdf" and content.startswith(b"%PDF-"))
        or (mime_type == "text/plain" and b"\x00" not in content[:4096])
        or (extension in {"docx", "xlsx", "pptx", "zip"} and content.startswith(b"PK"))
        or (extension in {"doc", "xls", "ppt"} and content.startswith(b"\xd0\xcf\x11\xe0"))
    ) or (
        (mime_type in {"video/mp4", "video/quicktime", "audio/mp4"} and len(content) > 12 and content[4:8] == b"ftyp")
        or (mime_type in {"video/webm", "audio/webm"} and content.startswith(b"\x1aE\xdf\xa3"))
        or (mime_type == "audio/ogg" and content.startswith(b"OggS"))
        or (mime_type == "audio/wav" and content.startswith(b"RIFF") and content[8:12] == b"WAVE")
        or (mime_type == "audio/mpeg" and (content.startswith(b"ID3") or content[:2] in {b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"}))
    )
    if not signatures_ok:
        raise HTTPException(400, "Nội dung tệp không khớp định dạng media đã khai báo.")
    media_id = uuid.uuid4()
    media = MediaFile(id=media_id, owner_id=owner_id, bucket=settings.R2_BUCKET_NAME, object_key=build_object_key(kind, owner_id, purpose, media_id, extension), original_name=original_name[:255], mime_type=mime_type, file_size=len(content), checksum_sha256=hashlib.sha256(content).hexdigest(), status=MediaStatus.PENDING)
    db.add(media)
    db.flush()
    try:
        get_r2_client().put_object(Bucket=media.bucket, Key=media.object_key, Body=content, ContentType=media.mime_type)
    except (BotoCoreError, ClientError) as exc:
        db.rollback()
        raise HTTPException(502, "Không thể tải media lên Cloudflare R2.") from exc
    media.status, media.uploaded_at = MediaStatus.READY, datetime.now(timezone.utc)
    db.commit()
    db.refresh(media)
    return media


def create_download_url(media: MediaFile) -> str:
    return get_r2_client().generate_presigned_url("get_object", Params={"Bucket": media.bucket, "Key": media.object_key}, ExpiresIn=settings.R2_PRESIGNED_URL_EXPIRE)
