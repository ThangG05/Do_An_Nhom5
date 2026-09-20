import argparse
import asyncio
import sys

from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal, dispose_engine
from app.models.rag import AIDocument, AIDocumentChunk, AIDocumentVersion


async def main() -> None:
    parser = argparse.ArgumentParser(description="Lexical diagnostic search in PostgreSQL knowledge data")
    parser.add_argument("text")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    pattern = f"%{args.text.strip()}%"
    try:
        async with AsyncSessionLocal() as session:
            versions = (await session.execute(
                select(AIDocument.title, AIDocumentVersion.id, AIDocumentVersion.status,
                       AIDocumentVersion.source_url)
                .join(AIDocument, AIDocument.id == AIDocumentVersion.document_id)
                .where(AIDocumentVersion.raw_content.ilike(pattern))
                .order_by(AIDocumentVersion.created_at.desc()).limit(args.limit)
            )).all()
            chunks = int(await session.scalar(
                select(func.count()).select_from(AIDocumentChunk)
                .where(AIDocumentChunk.content.ilike(pattern))
            ) or 0)
        print(f"versions={len(versions)} matching_chunks={chunks}")
        for title, version_id, status, source_url in versions:
            print(f"version_id={version_id} status={status.value} title={title}\nsource={source_url or '-'}")
    finally:
        await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
