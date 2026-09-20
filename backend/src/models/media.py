import uuid
from typing import Literal
from pydantic import BaseModel, Field

class PresignUploadRequest(BaseModel):
    purpose: Literal["avatar"]
    original_name: str = Field(min_length=1, max_length=255)
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]
    file_size: int = Field(gt=0, le=5 * 1024 * 1024)

class PresignUploadResponse(BaseModel):
    media_id: uuid.UUID
    upload_url: str
    expires_in: int
    headers: dict[str, str]

class CompleteUploadRequest(BaseModel):
    width: int | None = Field(default=None, gt=0, le=20000)
    height: int | None = Field(default=None, gt=0, le=20000)

class MediaResponse(BaseModel):
    media_id: uuid.UUID
    status: str
