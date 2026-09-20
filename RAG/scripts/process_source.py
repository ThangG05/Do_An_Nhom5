"""Run the post-crawl pipeline for one approved source."""
import argparse
import asyncio
import sys
from collections import Counter
from types import SimpleNamespace
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import AsyncSessionLocal, dispose_engine
from app.knowledge.chunking import DocumentChunkingService
from app.knowledge.indexing import DocumentIndexingService
from app.knowledge.references import extract_source_references
from app.models.crawler import AISourceURL
from app.models.enums import AIDocumentStatus
from app.models.rag import AIDocumentVersion
from app.rag.embeddings import get_embedding_provider
from app.services.qdrant import close_qdrant
from scripts.crawl import normalize_source
from scripts.index import sync_metadata


async def source_versions(source_id: UUID, status: AIDocumentStatus, limit: int) -> list[UUID]:
    async with AsyncSessionLocal() as session:
        return list((await session.scalars(
            select(AIDocumentVersion.id)
            .join(AISourceURL, AISourceURL.document_id == AIDocumentVersion.document_id)
            .where(AISourceURL.source_id == source_id, AIDocumentVersion.status == status)
            .order_by(AIDocumentVersion.created_at).limit(limit)
        )).all())


async def extract_references_with_retry(source_id: UUID, attempts: int = 3):
    for attempt in range(attempts):
        try:
            async with AsyncSessionLocal() as session:
                return await extract_source_references(session, source_id)
        except (SQLAlchemyError, TimeoutError):
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(2 ** attempt)
    raise AssertionError("unreachable")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize, chunk, index and reconcile one crawl source")
    parser.add_argument("--source-id", required=True, type=UUID)
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()
    try:
        await normalize_source(SimpleNamespace(source_id=str(args.source_id)))
        references = await extract_references_with_retry(args.source_id)
        print(f"references={references.references} resolved={references.resolved} missing={references.missing}")
        await sync_metadata(SimpleNamespace(source_id=str(args.source_id)))
        completed = failed = chunks = 0
        for version_id in await source_versions(args.source_id, AIDocumentStatus.PENDING, args.limit):
            async with AsyncSessionLocal() as session:
                service = DocumentChunkingService(session)
                try:
                    result = await service.process(version_id)
                    completed += 1; chunks += result.chunk_count
                except Exception as exc:
                    await service.mark_failed(version_id, exc); failed += 1
        embedder = get_embedding_provider()
        indexed = index_failed = points = 0
        index_errors: Counter[str] = Counter()
        try:
            for version_id in await source_versions(args.source_id, AIDocumentStatus.PROCESSING, args.limit):
                async with AsyncSessionLocal() as session:
                    try:
                        result = await DocumentIndexingService(session, embedder).process(version_id)
                        indexed += 1; points += result.point_count
                    except Exception as exc:
                        index_failed += 1
                        index_errors[type(exc).__name__] += 1
        finally:
            await embedder.close()
        print(f"pipeline=complete chunked_versions={completed} chunks={chunks} "
              f"chunk_failed={failed} indexed_versions={indexed} points={points} "
              f"index_failed={index_failed}")
        if index_errors:
            print("index_error_types=" + ",".join(
                f"{name}:{count}" for name, count in sorted(index_errors.items())
            ))
        if failed or index_failed:
            raise SystemExit(2)
    finally:
        await close_qdrant()
        await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
