"""Transactional bridge from PostgreSQL chunks to the Qdrant vector index."""
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from qdrant_client import models as qmodels
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.indexer.qdrant import QdrantDocumentIndex
from app.models.enums import AIDocumentStatus
from app.models.rag import AIDocument, AIDocumentChunk, AIDocumentVersion
from app.rag.embeddings import EmbeddingProvider
from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class IndexingResult:
    version_id: UUID
    point_count: int
    duplicate: bool
    status: AIDocumentStatus


def _value(item: Any) -> Any:
    return item.value if hasattr(item, "value") else item


def point_payload(document: AIDocument, version: AIDocumentVersion,
                  chunk: AIDocumentChunk, *, is_current: bool = True) -> dict[str, Any]:
    version_metadata = version.metadata_ or {}
    academic_year = version_metadata.get("academic_year") or document.academic_year
    published_at = version_metadata.get("published_at") or (
        document.published_at.isoformat() if document.published_at else None
    )
    return {
        "chunk_id": str(chunk.id), "document_id": str(document.id),
        "document_version_id": str(version.id), "document_code": document.document_code,
        "title": document.title, "content": chunk.content,
        "document_type": _value(document.document_type), "academic_year": academic_year,
        "issuer": document.issuer,
        "published_at": published_at,
        "effective_from": document.effective_from.isoformat() if document.effective_from else None,
        "effective_to": document.effective_to.isoformat() if document.effective_to else None,
        "visibility": _value(document.visibility),
        "group_id": str(document.group_id) if document.group_id else None,
        "source_url": version.source_url, "version_number": version.version_number,
        "page_start": chunk.page_start, "page_end": chunk.page_end,
        "section_title": chunk.section_title, "heading_path": chunk.heading_path,
        "chunk_index": chunk.chunk_index, "content_hash": chunk.content_hash,
        "is_current": is_current,
    }


class DocumentIndexingService:
    def __init__(self, session: AsyncSession, embedder: EmbeddingProvider,
                 index: QdrantDocumentIndex | None = None) -> None:
        self.session, self.embedder = session, embedder
        self.index = index or QdrantDocumentIndex()

    async def process(self, version_id: UUID) -> IndexingResult:
        row = (await self.session.execute(select(AIDocumentVersion, AIDocument).join(
            AIDocument, AIDocument.id == AIDocumentVersion.document_id
        ).where(AIDocumentVersion.id == version_id))).one_or_none()
        if row is None: raise ValueError("document version not found")
        version, document = row
        chunks = list((await self.session.scalars(select(AIDocumentChunk).where(
            AIDocumentChunk.document_version_id == version.id
        ).order_by(AIDocumentChunk.chunk_index))).all())
        if version.status == AIDocumentStatus.INDEXED:
            return IndexingResult(version.id, len(chunks), True, version.status)
        if version.status != AIDocumentStatus.PROCESSING: raise ValueError("version is not ready for indexing")
        if not chunks: raise ValueError("version has no chunks")
        vectors = await self.embedder.embed_documents([chunk.content for chunk in chunks], document.title)
        if len(vectors) != len(chunks): raise ValueError("embedding count does not match chunk count")
        point_ids = [chunk.qdrant_point_id for chunk in chunks]
        stale_started = False
        try:
            await self.index.ensure_collection()
            await self.index.mark_document_versions_stale(document.id); stale_started = True
            await self.index.upsert([qmodels.PointStruct(
                id=chunk.qdrant_point_id, vector=vector,
                payload=point_payload(document, version, chunk),
            ) for chunk, vector in zip(chunks, vectors, strict=True)])
            await self.session.execute(update(AIDocumentVersion).where(
                AIDocumentVersion.document_id == document.id,
                AIDocumentVersion.id != version.id,
                AIDocumentVersion.status == AIDocumentStatus.INDEXED,
            ).values(status=AIDocumentStatus.ARCHIVED))
            version.status = AIDocumentStatus.INDEXED
            version.embedding_model = get_settings().embedding_model
            version.indexed_at = datetime.now(UTC)
            version.error_message = None
            document.current_version_id = version.id
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            try: await self.index.delete(point_ids)
            except Exception: pass
            if stale_started:
                try: await self.index.restore_previous_version(document.id, version.id)
                except Exception: pass
            failed = await self.session.get(AIDocumentVersion, version.id)
            if failed:
                failed.error_message = type(exc).__name__[:200]
                await self.session.commit()
            raise
        return IndexingResult(version.id, len(chunks), False, version.status)


async def ready_version_ids(session: AsyncSession, limit: int = 100) -> list[UUID]:
    return list((await session.scalars(select(AIDocumentVersion.id).where(
        AIDocumentVersion.status == AIDocumentStatus.PROCESSING
    ).order_by(AIDocumentVersion.created_at).limit(limit))).all())
