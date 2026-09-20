import argparse
import asyncio
import sys
from uuid import UUID
from sqlalchemy import func, select
from app.db.session import AsyncSessionLocal, dispose_engine
from app.knowledge.chunking import DocumentChunkingService, pending_version_ids
from app.models.rag import AIDocumentChunk


async def process(args) -> None:
    async with AsyncSessionLocal() as session:
        ids = [UUID(args.version_id)] if args.version_id else await pending_version_ids(session, args.limit)
    completed = failed = skipped = chunks = 0
    for version_id in ids:
        async with AsyncSessionLocal() as session:
            service = DocumentChunkingService(session)
            try:
                result = await service.process(version_id, args.rebuild)
                completed += 1; skipped += int(result.skipped); chunks += result.chunk_count
                print(f"version_id={version_id} status={result.status.value} chunks={result.chunk_count} duplicate={str(result.duplicate).lower()} skipped={str(result.skipped).lower()}")
            except Exception as exc:
                await service.mark_failed(version_id, exc); failed += 1
                print(f"version_id={version_id} status=FAILED diagnostic={type(exc).__name__}")
    print(f"completed={completed} failed={failed} skipped={skipped} chunks={chunks}")


async def inspect(args) -> None:
    async with AsyncSessionLocal() as session:
        rows = (await session.scalars(select(AIDocumentChunk).where(
            AIDocumentChunk.document_version_id == UUID(args.version_id)
        ).order_by(AIDocumentChunk.chunk_index))).all()
        for row in rows:
            preview = row.content[:args.preview].replace("\n", " ")
            print(f"[{row.chunk_index}] tokens={row.token_count} pages={row.page_start}-{row.page_end} section={row.section_title or '-'} hash={row.content_hash[:12]}\n{preview}\n")
        print(f"chunks={len(rows)}")


async def validate(_) -> None:
    async with AsyncSessionLocal() as session:
        count, min_tokens, max_tokens, avg_tokens = (await session.execute(select(
            func.count(AIDocumentChunk.id), func.min(AIDocumentChunk.token_count),
            func.max(AIDocumentChunk.token_count), func.avg(AIDocumentChunk.token_count),
        ))).one()
        empty = int(await session.scalar(select(func.count()).select_from(AIDocumentChunk).where(
            func.length(func.trim(AIDocumentChunk.content)) == 0)) or 0)
        duplicate_hashes = int(await session.scalar(select(func.count()).select_from(
            select(AIDocumentChunk.document_version_id, AIDocumentChunk.content_hash)
            .group_by(AIDocumentChunk.document_version_id, AIDocumentChunk.content_hash)
            .having(func.count() > 1).subquery()
        )) or 0)
        print(f"chunks={count} empty={empty} duplicate_hash_groups={duplicate_hashes} min_tokens={min_tokens or 0} max_tokens={max_tokens or 0} avg_tokens={float(avg_tokens or 0):.1f}")


def make_parser():
    root = argparse.ArgumentParser(description="Chunk pending document versions without embedding")
    commands = root.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run"); run.add_argument("--version-id"); run.add_argument("--limit", type=int, default=100)
    run.add_argument("--rebuild", action="store_true"); run.set_defaults(handler=process)
    show = commands.add_parser("inspect"); show.add_argument("--version-id", required=True)
    show.add_argument("--preview", type=int, default=240); show.set_defaults(handler=inspect)
    check = commands.add_parser("validate"); check.set_defaults(handler=validate)
    return root


async def main() -> None:
    args = make_parser().parse_args()
    try: await args.handler(args)
    finally: await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
