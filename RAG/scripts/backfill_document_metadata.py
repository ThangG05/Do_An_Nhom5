"""Conservative metadata backfill with dry-run default and Qdrant payload synchronization."""
import argparse
import asyncio
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

from qdrant_client import models
from sqlalchemy import select

from app.db.session import AsyncSessionLocal, dispose_engine
from app.knowledge.crawler.metadata import infer_metadata
from app.models.rag import AIDocument, AIDocumentVersion
from app.models.crawler import AISource, AISourceURL
from app.services.qdrant import close_qdrant, get_qdrant_client, qdrant_retry
from app.core.config import get_settings
from app.knowledge.crawler.metadata import VIETNAM_TZ


def explicit_date(metadata: dict) -> datetime | None:
    value = metadata.get("published_at") or metadata.get("date_published")
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=VIETNAM_TZ)
    except ValueError:
        return None


def date_from_archived_url(url: str | None) -> datetime | None:
    """Extract only a complete date encoded by HVNH's archived-media filenames.

    The archive directory supplies month/year, while the filename must supply a
    day. A month-only path is deliberately not converted to an invented date.
    """
    decoded = unquote(url or "")
    archive = re.search(r"/([01]?\d)\.([12]\d{3})/system/archivedate/", decoded,
                        re.IGNORECASE)
    if not archive:
        return None
    month, year = int(archive.group(1)), int(archive.group(2))
    filename = decoded.rsplit("/", 1)[-1]
    candidates = [
        (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        for match in re.finditer(r"(?<!\d)([0-3]\d)([01]\d)([12]\d{3})(?!\d)", filename)
    ]
    candidates.extend(
        (int(match.group(1)), int(match.group(2)), year)
        for match in re.finditer(r"(?<!\d)([0-3]?\d)\.([01]?\d)(?!\d)", filename)
    )
    for day, candidate_month, candidate_year in candidates:
        if candidate_month != month or candidate_year != year:
            continue
        try:
            return datetime(year, month, day, tzinfo=VIETNAM_TZ)
        except ValueError:
            continue
    return None


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Commit high-confidence values; default is dry-run")
    parser.add_argument("--report", type=Path, default=Path("evals/results/metadata-backfill.json"))
    parser.add_argument("--include-unresolved", action="store_true",
                        help="Include unresolved rows in the JSON report for review")
    args = parser.parse_args()
    changes = []
    unresolved = []
    try:
        async with AsyncSessionLocal() as session:
            rows = (await session.execute(select(AIDocument, AIDocumentVersion).join(
                AIDocumentVersion, AIDocumentVersion.id == AIDocument.current_version_id
            ).where(
                AIDocument.deleted_at.is_(None),
                (AIDocument.academic_year.is_(None)) | (AIDocument.published_at.is_(None)),
            ))).all()
            for document, version in rows:
                decoded_title = unquote(document.title)
                decoded_url = unquote(version.source_url or "")
                inferred = infer_metadata(
                    f"{decoded_title} {decoded_url}",
                    version.raw_content or "",
                    explicit_date(version.metadata_ or {}) or date_from_archived_url(version.source_url),
                )
                update = {}
                if document.academic_year is None and inferred.academic_year:
                    update["academic_year"] = inferred.academic_year
                if document.published_at is None and inferred.published_at:
                    update["published_at"] = inferred.published_at
                if not update:
                    if args.include_unresolved:
                        source = (await session.execute(
                            select(AISource.name, AISource.academic_year)
                            .join(AISourceURL, AISourceURL.source_id == AISource.id)
                            .where(AISourceURL.document_id == document.id)
                            .limit(1)
                        )).first()
                        unresolved.append({
                            "document_id": str(document.id),
                            "title": document.title,
                            "source_url": version.source_url,
                            "version_metadata": version.metadata_ or {},
                            "missing": [name for name in ("academic_year", "published_at")
                                        if getattr(document, name) is None],
                            "source_name": source.name if source else None,
                            "source_academic_year": source.academic_year if source else None,
                        })
                    continue
                changes.append({"document_id": str(document.id), "title": document.title,
                                **{key: value.isoformat() if isinstance(value, datetime) else value
                                   for key, value in update.items()}})
                if args.apply:
                    for key, value in update.items():
                        setattr(document, key, value)
                    provenance = dict(document.metadata_ or {})
                    provenance["metadata_backfill"] = {"method": "conservative_extract_v2",
                                                       "fields": sorted(update)}
                    document.metadata_ = provenance
            if args.apply:
                await session.commit()
            else:
                await session.rollback()
        qdrant_synced = 0
        if args.apply and changes:
            client, collection = get_qdrant_client(), get_settings().qdrant_collection
            operations = []
            for change in changes:
                payload = {key: value for key, value in change.items() if key in {"academic_year", "published_at"}}
                operations.append(models.SetPayloadOperation(set_payload=models.SetPayload(
                    payload=payload, filter=models.Filter(must=[models.FieldCondition(
                        key="document_id", match=models.MatchValue(value=change["document_id"]))]))))
            for offset in range(0, len(operations), 50):
                batch = operations[offset:offset + 50]
                await qdrant_retry(lambda b=batch: client.batch_update_points(
                    collection_name=collection, update_operations=b, wait=True))
                qdrant_synced += len(batch)
        report = {"applied": args.apply, "candidates": len(changes),
                  "qdrant_synced": qdrant_synced, "changes": changes,
                  "unresolved": unresolved}
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"applied={str(args.apply).lower()} candidates={len(changes)} report={args.report}")
    finally:
        await close_qdrant()
        await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
