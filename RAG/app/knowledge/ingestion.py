"""Stage-2 local ingestion: persist document/version only; indexing is a later worker."""
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.knowledge.loader.pdf_loader import load_local_document
from app.models.enums import AIDocumentStatus, AIDocumentType, AIVisibility
from app.models.rag import AIDocument, AIDocumentVersion
from app.rag.chunker import normalize_text


@dataclass(frozen=True, slots=True)
class IngestionRequest:
    path: Path
    document_code: str
    title: str
    document_type: AIDocumentType = AIDocumentType.OTHER
    academic_year: str | None = None
    issuer: str | None = None
    published_at: datetime | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    source_url: str | None = None
    visibility: AIVisibility = AIVisibility.PUBLIC
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class IngestionResult:
    document_id: UUID
    version_id: UUID
    version_number: int
    chunk_count: int
    duplicate: bool
    status: AIDocumentStatus


class DocumentIngestionService:
    def __init__(self, session: AsyncSession) -> None: self.session = session

    async def ingest(self, request: IngestionRequest) -> IngestionResult:
        self._validate_request(request)
        loaded = load_local_document(request.path)
        content = normalize_text(loaded.content)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        await self.session.execute(select(func.pg_advisory_xact_lock(func.hashtext(request.document_code))))
        document = await self.session.scalar(select(AIDocument).where(
            AIDocument.document_code == request.document_code, AIDocument.deleted_at.is_(None)
        ).order_by(AIDocument.created_at).limit(1))
        if document is None:
            document = AIDocument(document_code=request.document_code, title=request.title,
                                  document_type=request.document_type, academic_year=request.academic_year,
                                  issuer=request.issuer, published_at=request.published_at,
                                  effective_from=request.effective_from, effective_to=request.effective_to,
                                  visibility=request.visibility, metadata_=request.metadata)
            self.session.add(document); await self.session.flush()
        existing = await self.session.scalar(select(AIDocumentVersion).where(
            AIDocumentVersion.document_id == document.id, AIDocumentVersion.content_hash == digest))
        if existing:
            await self.session.rollback()
            return IngestionResult(document.id, existing.id, existing.version_number, 0, True, existing.status)
        latest = await self.session.scalar(select(func.max(AIDocumentVersion.version_number)).where(
            AIDocumentVersion.document_id == document.id))
        version = AIDocumentVersion(document_id=document.id, version_number=int(latest or 0) + 1,
                                    source_type="LOCAL_FILE", source_url=request.source_url,
                                    file_object_key=request.path.name, mime_type=loaded.mime_type,
                                    content_hash=digest, raw_content=content,
                                    status=AIDocumentStatus.PENDING,
                                    metadata_={"original_filename": request.path.name})
        self.session.add(version); await self.session.commit()
        return IngestionResult(document.id, version.id, version.version_number, 0, False, version.status)

    @staticmethod
    def _validate_request(request: IngestionRequest) -> None:
        if not request.document_code.strip() or len(request.document_code) > 100: raise ValueError("document code must contain 1-100 characters")
        if not request.title.strip() or len(request.title) > 500: raise ValueError("title must contain 1-500 characters")
        if request.academic_year and not re.fullmatch(r"[0-9]{4}/[0-9]{4}", request.academic_year): raise ValueError("academic year must use YYYY/YYYY")
        if request.effective_from and request.effective_to and request.effective_to < request.effective_from: raise ValueError("effective_to must not precede effective_from")
        if any(value is not None and value.tzinfo is None for value in (request.published_at, request.effective_from, request.effective_to)): raise ValueError("timestamps must include a timezone")
        if request.source_url:
            source = urlsplit(request.source_url)
            if source.scheme != "https" or not source.hostname or source.username or source.password: raise ValueError("source URL must be an HTTPS URL without credentials")
