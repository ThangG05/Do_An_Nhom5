from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.crawler.extractors import ExtractedDocument
from app.knowledge.crawler.metadata import infer_metadata
from app.models.crawler import AISource, AISourceURL
from app.models.enums import AIDocumentStatus, AIVisibility
from app.models.rag import AIDocument, AIDocumentVersion


@dataclass(frozen=True, slots=True)
class VersionResult:
    document_id: UUID
    version_id: UUID
    version_number: int
    duplicate: bool


async def save_web_version(session: AsyncSession, source: AISource, source_url: AISourceURL,
                           extracted: ExtractedDocument, mime_type: str,
                           discovered_from: str | None = None) -> VersionResult:
    digest = hashlib.sha256(extracted.content.encode("utf-8")).hexdigest()
    inferred = infer_metadata(extracted.title, extracted.content, extracted.published_at)
    document_type = source.document_type if source.document_type.value != "OTHER" else inferred.document_type
    await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(source_url.canonical_url))))
    if source_url.document_id:
        document = await session.get(AIDocument, source_url.document_id)
    else:
        document = None
    if document is None:
        document = AIDocument(
            document_code=(source.metadata_ or {}).get("document_code") or f"WEB-{source_url.url_hash[:24]}",
            title=extracted.title[:500],
            document_type=document_type, academic_year=source.academic_year or inferred.academic_year,
            issuer=source.issuer or "Học viện Ngân hàng", published_at=inferred.published_at,
            visibility=AIVisibility.PUBLIC,
            metadata_={"canonical_url": source_url.canonical_url, "source_id": str(source.id)},
        )
        session.add(document)
        await session.flush()
        source_url.document_id = document.id
    existing = await session.scalar(select(AIDocumentVersion).where(
        AIDocumentVersion.document_id == document.id,
        AIDocumentVersion.content_hash == digest,
    ))
    now = datetime.now(UTC)
    source_url.content_hash = digest
    source_url.last_changed_at = now if existing is None else source_url.last_changed_at
    document.document_type = document_type
    document.academic_year = source.academic_year or inferred.academic_year
    document.published_at = inferred.published_at or document.published_at
    if existing is not None:
        if discovered_from and not (existing.metadata_ or {}).get("discovered_from"):
            existing.metadata_ = {**(existing.metadata_ or {}), "discovered_from": discovered_from}
        return VersionResult(document.id, existing.id, existing.version_number, True)
    latest = await session.scalar(select(func.max(AIDocumentVersion.version_number)).where(
        AIDocumentVersion.document_id == document.id
    ))
    source_type = "WEB"
    if mime_type == "application/pdf": source_type = "PDF"
    elif "wordprocessingml" in mime_type: source_type = "DOCX"
    elif "spreadsheetml" in mime_type: source_type = "XLSX"
    version = AIDocumentVersion(
        document_id=document.id, version_number=int(latest or 0) + 1,
        source_type=source_type, source_url=source_url.canonical_url,
        mime_type=mime_type or None, content_hash=digest, raw_content=extracted.content,
        status=AIDocumentStatus.PENDING,
        metadata_={"page_count": extracted.page_count, **extracted.metadata,
                   "academic_year": source.academic_year or inferred.academic_year,
                   "published_at": inferred.published_at.isoformat() if inferred.published_at else None,
                   **({"discovered_from": discovered_from} if discovered_from else {})},
    )
    session.add(version)
    document.title = extracted.title[:500]
    document.published_at = inferred.published_at or document.published_at
    await session.flush()
    return VersionResult(document.id, version.id, version.version_number, False)
