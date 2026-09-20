"""Extract or inspect cross-document references."""
import argparse
import asyncio
import sys
from uuid import UUID

from sqlalchemy import select

from app.db.session import AsyncSessionLocal, dispose_engine
from app.knowledge.references import extract_source_references
from app.models.rag import AIDocumentRelation


async def extract_command(args) -> None:
    async with AsyncSessionLocal() as session:
        result = await extract_source_references(session, UUID(args.source_id))
    print(f"documents={result.documents} references={result.references} resolved={result.resolved} missing={result.missing}")


async def missing_command(args) -> None:
    async with AsyncSessionLocal() as session:
        rows = (await session.scalars(
            select(AIDocumentRelation).where(AIDocumentRelation.target_document_id.is_(None))
            .order_by(AIDocumentRelation.referenced_number).limit(args.limit)
        )).all()
        grouped: dict[tuple[str, str], int] = {}
        for row in rows:
            key = (row.referenced_number, row.relation_type)
            grouped[key] = grouped.get(key, 0) + 1
        for (number, relation), count in grouped.items():
            print(f"number={number} relation={relation} occurrences={count}")
        print(f"missing_references={len(rows)} unique={len(grouped)}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Manage document reference graph")
    commands = parser.add_subparsers(dest="command", required=True)
    extract_parser = commands.add_parser("extract")
    extract_parser.add_argument("--source-id", required=True)
    extract_parser.set_defaults(handler=extract_command)
    missing_parser = commands.add_parser("missing")
    missing_parser.add_argument("--limit", type=int, default=100)
    missing_parser.set_defaults(handler=missing_command)
    args = parser.parse_args()
    try:
        await args.handler(args)
    finally:
        await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
