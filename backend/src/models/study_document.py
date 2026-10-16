import uuid
from typing import Literal

from pydantic import BaseModel, Field


class SubjectResponse(BaseModel):
    id: uuid.UUID
    code: str | None
    name: str
    institution: str
    source_note: str
    is_active: bool
    category: Literal["GENERAL", "SPECIALIZED"] = "SPECIALIZED"
    needs_review: bool = False
    major_ids: list[uuid.UUID] = Field(default_factory=list)


class MajorResponse(BaseModel):
    id: uuid.UUID
    code: str | None
    name: str
    subject_count: int


class SubjectUpsertRequest(BaseModel):
    id: uuid.UUID | None = None
    code: str | None = Field(default=None, min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=255)
    source_note: str = Field(min_length=5, max_length=500)
    is_active: bool = True
    category: Literal["GENERAL", "SPECIALIZED"] = "SPECIALIZED"
    needs_review: bool = False
    major_ids: list[uuid.UUID] | None = None


class StudyDocumentFileResponse(BaseModel):
    id: uuid.UUID
    original_name: str
    mime_type: str
    extension: str
    size_bytes: int


class StudyDocumentResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    subject_id: uuid.UUID
    subject_code: str | None
    subject_name: str
    uploaded_by: uuid.UUID
    uploader_name: str
    title: str
    description: str | None
    status: Literal["PENDING", "APPROVED", "REJECTED"]
    total_bytes: int
    reviewed_at: str | None
    rejection_reason: str | None
    created_at: str
    files: list[StudyDocumentFileResponse]


class StudyDocumentDecision(BaseModel):
    decision: Literal["APPROVE", "REJECT"]
    reason: str | None = Field(default=None, max_length=2000)


class StudyDocumentDownload(BaseModel):
    url: str
    expires_in: int
