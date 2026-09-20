"""Export compact current-document evidence for manual gold-set curation."""
import argparse
import asyncio
import json
from pathlib import Path
import sys

from sqlalchemy import select

from app.db.session import AsyncSessionLocal, dispose_engine
from app.models.rag import AIDocument, AIDocumentChunk, AIDocumentVersion
from app.models.enums import AIDocumentStatus


async def main() -> None:
    parser = argparse.ArgumentParser(description="Export indexed HVNH evidence candidates")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("evals/results/gold-candidates.json"))
    args = parser.parse_args()
    try:
        async with AsyncSessionLocal() as session:
            rows = (await session.execute(
                select(AIDocument, AIDocumentVersion, AIDocumentChunk)
                .join(AIDocumentVersion, AIDocumentVersion.id == AIDocument.current_version_id)
                .join(AIDocumentChunk, AIDocumentChunk.document_version_id == AIDocumentVersion.id)
                .where(AIDocument.deleted_at.is_(None),
                       AIDocumentVersion.status == AIDocumentStatus.INDEXED)
                .order_by(AIDocument.document_type, AIDocument.published_at.desc().nullslast(),
                          AIDocument.title, AIDocumentChunk.chunk_index)
            )).all()
        grouped = {}
        for document, version, chunk in rows:
            key = str(document.id)
            if key not in grouped:
                if len(grouped) >= args.limit:
                    continue
                grouped[key] = {
                    "document_id": key, "version_id": str(version.id), "title": document.title,
                    "document_type": document.document_type.value, "academic_year": document.academic_year,
                    "published_at": document.published_at.isoformat() if document.published_at else None,
                    "issuer": document.issuer, "source_url": version.source_url, "chunks": [],
                }
            if len(grouped[key]["chunks"]) < 4:
                grouped[key]["chunks"].append(chunk.content)
        payload = []
        for item in grouped.values():
            chunks = item.pop("chunks")
            item["evidence_excerpt"] = "\n\n".join(chunks)[:6000]
            payload.append(item)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"candidates={len(payload)} output={args.output}")
    finally:
        await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
