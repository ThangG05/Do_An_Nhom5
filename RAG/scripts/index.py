import argparse
import asyncio
import sys
from uuid import UUID
from qdrant_client import models as qmodels
from sqlalchemy import func, select
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, dispose_engine
from app.knowledge.indexer.qdrant import QdrantDocumentIndex
from app.knowledge.indexing import DocumentIndexingService, ready_version_ids
from app.knowledge.indexing import point_payload
from app.knowledge.crawler.metadata import infer_metadata
from app.models.enums import AIDocumentStatus
from app.models.crawler import AISourceURL
from app.models.rag import AIDocument, AIDocumentChunk, AIDocumentVersion
from app.rag.embeddings import get_embedding_provider
from app.services.qdrant import close_qdrant, get_qdrant_client, qdrant_retry


def stale_point_ids(indexed_chunk_ids: set[str], qdrant_point_ids: set[str]) -> list[UUID]:
    return sorted((UUID(value) for value in qdrant_point_ids - indexed_chunk_ids), key=str)


async def run(args) -> None:
    embedder = get_embedding_provider()
    try:
        async with AsyncSessionLocal() as session:
            ids = [UUID(args.version_id)] if args.version_id else await ready_version_ids(session, args.limit)
        completed = failed = points = 0
        for version_id in ids:
            async with AsyncSessionLocal() as session:
                try:
                    result = await DocumentIndexingService(session, embedder).process(version_id)
                    completed += 1; points += result.point_count
                    print(f"version_id={version_id} status={result.status.value} points={result.point_count} duplicate={str(result.duplicate).lower()}")
                except Exception as exc:
                    failed += 1
                    print(f"version_id={version_id} status=ERROR diagnostic={type(exc).__name__}")
        print(f"completed={completed} failed={failed} points={points}")
    finally:
        await embedder.close()


async def validate(_) -> None:
    index = QdrantDocumentIndex(); await index.ensure_collection()
    client = get_qdrant_client()
    qdrant_count = (await client.count(index.collection, exact=True)).count
    current_qdrant_count = (await client.count(
        index.collection,
        count_filter=qmodels.Filter(must=[qmodels.FieldCondition(
            key="is_current", match=qmodels.MatchValue(value=True)
        )]),
        exact=True,
    )).count
    details = await client.get_collection(index.collection)
    dimensions = getattr(details.config.params.vectors, "size", None)
    required_indexes = {"document_id", "document_version_id", "document_type", "academic_year",
                        "visibility", "group_id", "is_current", "published_at"}
    missing_indexes = sorted(required_indexes - set(details.payload_schema))
    sample, _ = await client.scroll(index.collection, limit=1, with_payload=True, with_vectors=True)
    sample_ok = False
    if sample:
        vector = sample[0].vector
        vector_size = len(vector) if isinstance(vector, list) else 0
        payload = sample[0].payload or {}
        sample_ok = vector_size == index.settings.embedding_dimensions and all(
            key in payload for key in ("chunk_id", "document_id", "document_version_id", "title", "content", "source_url", "is_current")
        )
    async with AsyncSessionLocal() as session:
        postgres_count = int(await session.scalar(select(func.count()).select_from(AIDocumentChunk).join(
            AIDocumentVersion, AIDocumentVersion.id == AIDocumentChunk.document_version_id
        ).where(AIDocumentVersion.status == AIDocumentStatus.INDEXED)) or 0)
        indexed_versions = int(await session.scalar(select(func.count()).select_from(AIDocumentVersion).where(
            AIDocumentVersion.status == AIDocumentStatus.INDEXED)) or 0)
    valid = postgres_count == current_qdrant_count and qdrant_count >= current_qdrant_count \
        and dimensions == index.settings.embedding_dimensions and not missing_indexes and sample_ok
    print(f"postgres_current_chunks={postgres_count} qdrant_current_points={current_qdrant_count} "
          f"qdrant_total_points={qdrant_count} historical_points={qdrant_count-current_qdrant_count} "
          f"indexed_versions={indexed_versions} dimensions={dimensions} "
          f"missing_indexes={','.join(missing_indexes) or '-'} sample_payload={str(sample_ok).lower()} "
          f"valid={str(valid).lower()}")


async def index_history(args) -> None:
    """Index archived chunks for temporal questions without changing current-version state."""
    index = QdrantDocumentIndex()
    await index.ensure_collection()
    client = get_qdrant_client()
    current_count = int((await client.count(index.collection, exact=True)).count)
    if current_count >= args.target_points:
        print(f"target={args.target_points} before={current_count} after={current_count} added=0")
        return

    remote: set[str] = set()
    offset = None
    while True:
        points, offset = await client.scroll(
            index.collection, limit=256, offset=offset,
            with_payload=False, with_vectors=False,
        )
        remote.update(str(point.id) for point in points)
        if offset is None:
            break

    embedder = get_embedding_provider()
    added = versions = 0
    try:
        async with AsyncSessionLocal() as session:
            rows = (await session.execute(
                select(AIDocumentVersion, AIDocument)
                .join(AIDocument, AIDocument.id == AIDocumentVersion.document_id)
                .where(
                    AIDocumentVersion.status == AIDocumentStatus.ARCHIVED,
                    AIDocument.deleted_at.is_(None),
                )
                .order_by(AIDocumentVersion.created_at.desc())
            )).all()
            for version, document in rows:
                if current_count + added >= args.target_points:
                    break
                if (document.metadata_ or {}).get("retrieval_excluded") is True:
                    continue
                if (version.metadata_ or {}).get("security_review") == "QUARANTINED":
                    continue
                chunks = list((await session.scalars(
                    select(AIDocumentChunk)
                    .where(AIDocumentChunk.document_version_id == version.id)
                    .order_by(AIDocumentChunk.chunk_index)
                )).all())
                missing = [chunk for chunk in chunks if str(chunk.qdrant_point_id) not in remote]
                if not missing:
                    continue
                remaining = args.target_points - current_count - added
                missing = missing[:remaining]
                inferred = infer_metadata(document.title, version.raw_content or "")
                metadata = dict(version.metadata_ or {})
                if not metadata.get("academic_year"):
                    metadata["academic_year"] = inferred.academic_year or document.academic_year
                if not metadata.get("published_at"):
                    metadata["published_at"] = (
                        inferred.published_at.isoformat() if inferred.published_at else
                        (document.published_at.isoformat() if document.published_at else None)
                    )
                version.metadata_ = metadata
                vectors = await embedder.embed_documents(
                    [chunk.content for chunk in missing], document.title
                )
                await index.upsert([
                    qmodels.PointStruct(
                        id=chunk.qdrant_point_id,
                        vector=vector,
                        payload=point_payload(document, version, chunk, is_current=False),
                    )
                    for chunk, vector in zip(missing, vectors, strict=True)
                ])
                remote.update(str(chunk.qdrant_point_id) for chunk in missing)
                added += len(missing)
                versions += 1
            await session.commit()
    finally:
        await embedder.close()
    print(f"target={args.target_points} before={current_count} after={current_count+added} "
          f"added={added} archived_versions={versions}")


async def info(_) -> None:
    index = QdrantDocumentIndex()
    exists = await get_qdrant_client().collection_exists(index.collection)
    if not exists:
        print(f"collection={index.collection} exists=false"); return
    details = await get_qdrant_client().get_collection(index.collection)
    vectors = details.config.params.vectors
    print(f"collection={index.collection} exists=true dimensions={getattr(vectors, 'size', 'named')} points={details.points_count or 0}")


async def migrate_empty(_) -> None:
    index = QdrantDocumentIndex(); client = get_qdrant_client()
    if await client.collection_exists(index.collection):
        details = await client.get_collection(index.collection)
        if int(details.points_count or 0) != 0:
            raise ValueError("refusing to replace a non-empty collection")
        await client.delete_collection(index.collection)
    await index.ensure_collection()
    print(f"collection={index.collection} dimensions={index.settings.embedding_dimensions} migrated=true")


async def prune(args) -> None:
    """Remove vectors whose chunks no longer belong to an INDEXED PostgreSQL version."""
    index = QdrantDocumentIndex()
    client = get_qdrant_client()
    if not await client.collection_exists(index.collection):
        print(f"collection={index.collection} exists=false stale=0 deleted=0")
        return
    async with AsyncSessionLocal() as session:
        indexed = {
            str(value) for value in (await session.scalars(
                select(AIDocumentChunk.qdrant_point_id)
                .join(AIDocumentVersion, AIDocumentVersion.id == AIDocumentChunk.document_version_id)
                .where(AIDocumentVersion.status.in_((AIDocumentStatus.INDEXED, AIDocumentStatus.ARCHIVED)))
            )).all()
        }
    remote: set[str] = set()
    offset = None
    while True:
        points, offset = await client.scroll(
            index.collection, limit=256, offset=offset,
            with_payload=False, with_vectors=False,
        )
        remote.update(str(point.id) for point in points)
        if offset is None:
            break
    stale = stale_point_ids(indexed, remote)
    if args.apply:
        for start in range(0, len(stale), 256):
            await index.delete(stale[start:start + 256])
    print(f"collection={index.collection} indexed={len(indexed)} remote={len(remote)} "
          f"stale={len(stale)} deleted={len(stale) if args.apply else 0} apply={str(args.apply).lower()}")


async def sync_metadata(args) -> None:
    source_id = UUID(args.source_id)
    async with AsyncSessionLocal() as session:
        documents = list((await session.scalars(
            select(AIDocument).join(AISourceURL, AISourceURL.document_id == AIDocument.id)
            .where(AISourceURL.source_id == source_id).distinct()
        )).all())
    client = get_qdrant_client(); collection = get_settings().qdrant_collection
    operations = []
    for document in documents:
        operations.append(qmodels.SetPayloadOperation(set_payload=qmodels.SetPayload(
            payload={
                "document_type": document.document_type.value,
                "academic_year": document.academic_year,
                "issuer": document.issuer,
                "published_at": document.published_at.isoformat() if document.published_at else None,
                "effective_from": document.effective_from.isoformat() if document.effective_from else None,
                "effective_to": document.effective_to.isoformat() if document.effective_to else None,
                "visibility": document.visibility.value,
                "group_id": str(document.group_id) if document.group_id else None,
            }, filter=qmodels.Filter(must=[qmodels.FieldCondition(
                key="document_id", match=qmodels.MatchValue(value=str(document.id))
            )]))))
    for offset in range(0, len(operations), 50):
        batch = operations[offset:offset + 50]
        await qdrant_retry(lambda b=batch: client.batch_update_points(
            collection_name=collection, update_operations=b, wait=True,
        ))
    print(f"source_id={source_id} documents={len(documents)} metadata_synced=true")


def make_parser():
    root = argparse.ArgumentParser(description="Embed PROCESSING chunks and index them in Qdrant")
    commands = root.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("run"); execute.add_argument("--version-id"); execute.add_argument("--limit", type=int, default=100); execute.set_defaults(handler=run)
    check = commands.add_parser("validate"); check.set_defaults(handler=validate)
    details = commands.add_parser("info"); details.set_defaults(handler=info)
    history = commands.add_parser("history", help="Index archived versions for temporal retrieval")
    history.add_argument("--target-points", type=int, default=1000)
    history.set_defaults(handler=index_history)
    migrate = commands.add_parser("migrate-empty"); migrate.set_defaults(handler=migrate_empty)
    cleanup = commands.add_parser("prune", help="Delete Qdrant points not backed by an INDEXED PostgreSQL chunk")
    cleanup.add_argument("--apply", action="store_true"); cleanup.set_defaults(handler=prune)
    metadata = commands.add_parser("sync-metadata")
    metadata.add_argument("--source-id", required=True); metadata.set_defaults(handler=sync_metadata)
    return root


async def main() -> None:
    args = make_parser().parse_args()
    try: await args.handler(args)
    finally: await close_qdrant(); await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
