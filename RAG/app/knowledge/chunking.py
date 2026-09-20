"""Database chunking stage. This module never calls an LLM, embedding model, or Qdrant."""
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.llm.security import InputKind, PromptGuard, PromptSecurityError
from app.models.enums import AIDocumentStatus
from app.models.rag import AIDocument, AIDocumentChunk, AIDocumentVersion
from app.rag.chunker import CHUNKING_VERSION, chunk_text


@dataclass(frozen=True, slots=True)
class ChunkingResult:
    version_id: UUID
    chunk_count: int
    duplicate: bool
    skipped: bool
    status: AIDocumentStatus


def _pages_for(metadata: dict, start: int, end: int) -> tuple[int | None, int | None]:
    pages = [int(row[0]) for row in metadata.get("page_ranges", [])
             if len(row) == 3 and int(row[1]) < end and int(row[2]) > start]
    return (min(pages), max(pages)) if pages else (None, None)


class DocumentChunkingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.guard = PromptGuard(self.settings.llm_max_input_chars, self.settings.llm_max_context_chars)

    async def process(self, version_id: UUID, rebuild: bool = False) -> ChunkingResult:
        await self.session.execute(select(func.pg_advisory_xact_lock(func.hashtext(str(version_id)))))
        row = (await self.session.execute(
            select(AIDocumentVersion, AIDocument)
            .join(AIDocument, AIDocument.id == AIDocumentVersion.document_id)
            .where(AIDocumentVersion.id == version_id)
            .with_for_update()
        )).one_or_none()
        if row is None: raise ValueError("document version not found")
        version, document = row
        if (document.metadata_ or {}).get("retrieval_excluded") is True:
            version.status = AIDocumentStatus.ARCHIVED
            version.metadata_ = {**(version.metadata_ or {}), "chunk_skip_reason": "retrieval_excluded"}
            await self.session.commit()
            return ChunkingResult(version.id, 0, False, True, version.status)
        count = int(await self.session.scalar(select(func.count()).select_from(AIDocumentChunk).where(
            AIDocumentChunk.document_version_id == version.id)) or 0)
        if count and not rebuild:
            await self.session.commit()
            return ChunkingResult(version.id, count, True, False, version.status)
        if rebuild and version.status == AIDocumentStatus.INDEXED:
            raise ValueError("indexed versions cannot be rebuilt before vector de-indexing")
        if not version.raw_content: raise ValueError("document version has no raw content")
        chunks = chunk_text(version.raw_content, self.settings.chunk_size_chars,
                            self.settings.chunk_overlap_chars)
        security_approved = (version.metadata_ or {}).get("security_review") == "APPROVED"
        if not security_approved:
            for chunk in chunks:
                self.guard.inspect(chunk.content, InputKind.CONTEXT)
        if rebuild:
            await self.session.execute(delete(AIDocumentChunk).where(
                AIDocumentChunk.document_version_id == version.id))
        for chunk in chunks:
            page_start, page_end = _pages_for(version.metadata_ or {}, chunk.start_offset, chunk.end_offset)
            self.session.add(AIDocumentChunk(
                document_version_id=version.id, chunk_index=chunk.index,
                content=chunk.content, content_hash=chunk.content_hash,
                token_count=chunk.token_count, page_start=page_start, page_end=page_end,
                section_title=chunk.section_title, heading_path=list(chunk.heading_path),
                start_offset=chunk.start_offset, end_offset=chunk.end_offset,
                metadata_={"chunking_version": CHUNKING_VERSION},
            ))
        version.status = AIDocumentStatus.PROCESSING
        version.chunking_version = CHUNKING_VERSION
        version.error_message = None
        await self.session.commit()
        return ChunkingResult(version.id, len(chunks), False, False, version.status)

    async def mark_failed(self, version_id: UUID, exc: Exception) -> None:
        await self.session.rollback()
        version = await self.session.get(AIDocumentVersion, version_id)
        if version:
            version.status = AIDocumentStatus.FAILED
            version.error_message = type(exc).__name__[:200]
            if isinstance(exc, PromptSecurityError):
                version.metadata_ = {
                    **dict(version.metadata_ or {}),
                    "security_review": "QUARANTINED",
                    "security_reason": exc.code,
                }
            await self.session.commit()


async def pending_version_ids(session: AsyncSession, limit: int = 100) -> list[UUID]:
    return list((await session.scalars(
        select(AIDocumentVersion.id)
        .where(AIDocumentVersion.status == AIDocumentStatus.PENDING)
        .order_by(AIDocumentVersion.created_at)
        .limit(limit)
    )).all())
