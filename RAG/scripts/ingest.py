"""Admin-only CLI for ingesting a local knowledge document."""
import argparse
import asyncio
from datetime import datetime
from pathlib import Path

from app.db.session import AsyncSessionLocal, dispose_engine
from app.knowledge.ingestion import DocumentIngestionService, IngestionRequest
from app.models.enums import AIDocumentType, AIVisibility
from app.services.qdrant import close_qdrant


def optional_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest one local HVNH knowledge document")
    parser.add_argument("path", type=Path)
    parser.add_argument("--code", required=True, help="Stable logical document code")
    parser.add_argument("--title", required=True)
    parser.add_argument("--type", choices=[item.value for item in AIDocumentType], default="OTHER")
    parser.add_argument("--academic-year", help="Format: 2025/2026")
    parser.add_argument("--issuer")
    parser.add_argument("--source-url")
    parser.add_argument("--published-at", help="ISO-8601 timestamp")
    parser.add_argument("--effective-from", help="ISO-8601 timestamp")
    parser.add_argument("--effective-to", help="ISO-8601 timestamp")
    parser.add_argument("--visibility", choices=[item.value for item in AIVisibility], default="PUBLIC")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    try:
        async with AsyncSessionLocal() as session:
            result = await DocumentIngestionService(session).ingest(IngestionRequest(
                path=args.path, document_code=args.code, title=args.title,
                document_type=AIDocumentType(args.type), academic_year=args.academic_year,
                issuer=args.issuer, source_url=args.source_url,
                published_at=optional_datetime(args.published_at),
                effective_from=optional_datetime(args.effective_from),
                effective_to=optional_datetime(args.effective_to),
                visibility=AIVisibility(args.visibility),
            ))
        print(f"ingestion={result.status.value.lower()}")
        print(f"document_id={result.document_id}")
        print(f"version_id={result.version_id}")
        print(f"version={result.version_number}, chunks={result.chunk_count}, duplicate={str(result.duplicate).lower()}")
    except Exception as exc:
        print("ingestion=error")
        print(f"diagnostic={type(exc).__name__}")
        raise SystemExit(1) from None
    finally:
        await close_qdrant()
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
