import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class StudyDocumentReportCreate(BaseModel):
    reason: str = Field(min_length=5, max_length=3000)


class StudyDocumentReportDecision(BaseModel):
    decision: Literal["REMOVE_DOCUMENT", "DISMISS"]
    note: str = Field(min_length=3, max_length=3000)


class StudyDocumentReportResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    document_id: uuid.UUID
    title: str
    subject_code: str | None
    subject_name: str
    uploader_name: str
    reporter_name: str
    reason: str
    status: Literal["OPEN", "RESOLVED", "DISMISSED"]
    resolution_note: str | None
    handled_by_name: str | None
    created_at: datetime
    document_deleted: bool
