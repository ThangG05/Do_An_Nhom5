"""Document-library endpoints are intentionally separate from ordinary group posts."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from src.api.dependencies import CurrentGroupAdmin, CurrentSuperAdmin, CurrentUser
from src.db.session import get_db
from src.models.study_document import (StudyDocumentDecision, StudyDocumentDownload,
                                       StudyDocumentResponse, SubjectResponse, SubjectUpsertRequest)
from src.services import study_document_service as library

router = APIRouter(tags=["Study document library"])
Db = Annotated[Session, Depends(get_db)]


@router.get("/subjects", response_model=list[SubjectResponse])
def subjects(user: CurrentUser, db: Db, q: Annotated[str, Query(max_length=100)] = ""):
    return library.list_subjects(db, q)


@router.get("/admin/subjects", response_model=list[SubjectResponse])
def admin_subjects(admin: CurrentSuperAdmin, db: Db, q: Annotated[str, Query(max_length=100)] = ""):
    return library.list_subjects(db, q, include_inactive=True)


@router.put("/admin/subjects", response_model=SubjectResponse)
def put_subject(payload: SubjectUpsertRequest, admin: CurrentSuperAdmin, db: Db):
    return library.upsert_subject(db, payload.code, payload.name, payload.source_note, payload.is_active)


@router.get("/groups/{group_id}/library", response_model=list[StudyDocumentResponse])
def documents(group_id: uuid.UUID, user: CurrentUser, db: Db,
              q: Annotated[str, Query(max_length=100)] = "", subject_id: uuid.UUID | None = None,
              limit: Annotated[int, Query(ge=1, le=50)] = 30,
              offset: Annotated[int, Query(ge=0)] = 0):
    return library.list_documents(db, group_id, user, query=q, subject_id=subject_id,
                                  limit=limit, offset=offset)


@router.get("/groups/{group_id}/library/mine", response_model=list[StudyDocumentResponse])
def my_documents(group_id: uuid.UUID, user: CurrentUser, db: Db,
                 limit: Annotated[int, Query(ge=1, le=50)] = 30,
                 offset: Annotated[int, Query(ge=0)] = 0):
    return library.list_documents(db, group_id, user, mine=True, limit=limit, offset=offset)


@router.get("/groups/{group_id}/library/admin/pending", response_model=list[StudyDocumentResponse])
def pending_documents(group_id: uuid.UUID, admin: CurrentGroupAdmin, db: Db,
                      limit: Annotated[int, Query(ge=1, le=50)] = 30,
                      offset: Annotated[int, Query(ge=0)] = 0):
    return library.list_documents(db, group_id, admin, pending=True, limit=limit, offset=offset)


@router.post("/groups/{group_id}/library", response_model=StudyDocumentResponse, status_code=201)
def share_document(group_id: uuid.UUID, user: CurrentUser, db: Db,
                   subject_id: Annotated[uuid.UUID, Form()], title: Annotated[str, Form(min_length=2, max_length=255)],
                   files: Annotated[list[UploadFile], File()],
                   description: Annotated[str | None, Form(max_length=2000)] = None):
    return library.create_document(db, group_id, user, subject_id, title, description, files)


@router.post("/groups/{group_id}/library/admin/cleanup")
def cleanup_rejected(group_id: uuid.UUID, admin: CurrentGroupAdmin, db: Db):
    return library.cleanup_rejected_files(db, group_id, admin)


@router.get("/groups/{group_id}/library/{document_id}", response_model=StudyDocumentResponse)
def document_detail(group_id: uuid.UUID, document_id: uuid.UUID, user: CurrentUser, db: Db):
    return library.get_document(db, group_id, document_id, user)


@router.get("/groups/{group_id}/library/{document_id}/files/{file_id}/download",
            response_model=StudyDocumentDownload)
def download(group_id: uuid.UUID, document_id: uuid.UUID, file_id: uuid.UUID,
             user: CurrentUser, db: Db, preview: bool = False):
    return StudyDocumentDownload(url=library.file_download(db, group_id, document_id, file_id, user,
                                                           preview=preview),
                                 expires_in=min(library.settings.R2_PRESIGNED_URL_EXPIRE, 300))


@router.patch("/groups/{group_id}/library/admin/{document_id}", response_model=StudyDocumentResponse)
def moderate(group_id: uuid.UUID, document_id: uuid.UUID, payload: StudyDocumentDecision,
             admin: CurrentGroupAdmin, db: Db):
    return library.moderate_document(db, group_id, document_id, admin,
                                     payload.decision == "APPROVE", payload.reason)
