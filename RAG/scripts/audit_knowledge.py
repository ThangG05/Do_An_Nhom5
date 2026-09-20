"""Read-only quality gate for crawled, chunked and indexed knowledge."""
import argparse
import asyncio
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
import sys

from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal, dispose_engine
from app.models.crawler import AICrawlItem, AICrawlRun, AISource, AISourceURL
from app.models.enums import AIDocumentStatus
from app.models.rag import AIDocument, AIDocumentChunk, AIDocumentVersion


async def collect() -> dict:
    async with AsyncSessionLocal() as session:
        sources = list((await session.scalars(select(AISource).order_by(AISource.name))).all())
        documents = (await session.execute(select(
            AIDocument.id, AIDocument.academic_year, AIDocument.published_at, AIDocument.issuer
        ).where(AIDocument.deleted_at.is_(None)))).all()
        versions = (await session.execute(select(
            AIDocumentVersion.id, AIDocumentVersion.status, AIDocumentVersion.source_url,
            AIDocumentVersion.error_message,
        ))).all()
        chunk_counts = dict((await session.execute(
            select(AIDocumentChunk.document_version_id, func.count(AIDocumentChunk.id))
            .group_by(AIDocumentChunk.document_version_id)
        )).all())
        latest_item = select(
            AICrawlItem.url, AICrawlItem.error_code, AICrawlItem.content_type,
            AICrawlItem.status,
            func.row_number().over(
                partition_by=AICrawlItem.source_url_id,
                order_by=AICrawlItem.finished_at.desc().nullslast(),
            ).label("row_number"),
        ).subquery()
        rejected = Counter(dict((await session.execute(
            select(latest_item.c.error_code, func.count())
            .where(latest_item.c.row_number == 1, latest_item.c.status == "REJECTED")
            .group_by(latest_item.c.error_code)
        )).all()))
        rejected_details = [
            {"url": url, "error_code": error_code or "UNKNOWN", "content_type": content_type}
            for url, error_code, content_type in (await session.execute(
                select(latest_item.c.url, latest_item.c.error_code, latest_item.c.content_type)
                .where(latest_item.c.row_number == 1, latest_item.c.status == "REJECTED")
                .limit(100)
            )).all()
        ]
        latest_runs = {}
        for run in (await session.execute(select(
                AICrawlRun.id, AICrawlRun.source_id, AICrawlRun.status, AICrawlRun.queued_at
        ).order_by(AICrawlRun.source_id, AICrawlRun.queued_at.desc()))).all():
            latest_runs.setdefault(str(run.source_id), run)
        source_version_rows = (await session.execute(
            select(AISourceURL.source_id, AIDocumentVersion.status,
                   func.count(func.distinct(AIDocumentVersion.id)))
            .join(AIDocumentVersion, AIDocumentVersion.document_id == AISourceURL.document_id)
            .group_by(AISourceURL.source_id, AIDocumentVersion.status)
        )).all()
        source_versions: dict[str, dict[str, int]] = {}
        for source_id, status, count in source_version_rows:
            source_versions.setdefault(str(source_id), {})[status.value] = int(count)

    now = datetime.now(UTC)
    status_counts = Counter(version.status.value for version in versions)
    version_errors = Counter(
        (version.error_message or "UNKNOWN")
        for version in versions
        if version.error_message
    )
    missing = {
        "academic_year": sum(document.academic_year is None for document in documents),
        "published_at": sum(document.published_at is None for document in documents),
        "issuer": sum(not document.issuer for document in documents),
        "source_url": sum(not version.source_url for version in versions),
    }
    async with AsyncSessionLocal() as session:
        quarantined = int(await session.scalar(select(func.count()).select_from(AIDocumentVersion).where(
            AIDocumentVersion.metadata_["security_review"].astext == "QUARANTINED")) or 0)
    indexed_without_chunks = sum(version.status == AIDocumentStatus.INDEXED
                                 and chunk_counts.get(version.id, 0) == 0 for version in versions)
    processing_without_chunks = sum(version.status == AIDocumentStatus.PROCESSING
                                    and chunk_counts.get(version.id, 0) == 0 for version in versions)
    source_rows = []
    for source in sources:
        run = latest_runs.get(str(source.id))
        source_rows.append({
            "id": str(source.id), "name": source.name, "enabled": source.enabled,
            "base_url": source.base_url,
            "overdue": bool(source.enabled and source.next_crawl_at and source.next_crawl_at <= now),
            "latest_run_status": run.status if run else None,
            "latest_run_id": str(run.id) if run else None,
            "version_statuses": source_versions.get(str(source.id), {}),
        })
    return {
        "generated_at": now.isoformat(),
        "counts": {"sources": len(sources), "enabled_sources": sum(item.enabled for item in sources),
                   "documents": len(documents), "versions": len(versions),
                   "chunks": sum(chunk_counts.values()), "quarantined": quarantined},
        "version_statuses": dict(sorted(status_counts.items())),
        "version_error_types": dict(sorted(version_errors.items())),
        "missing_metadata": missing,
        "integrity": {"indexed_without_chunks": indexed_without_chunks,
                      "processing_without_chunks": processing_without_chunks},
        "rejected_crawl_items": dict(sorted((key or "UNKNOWN", value) for key, value in rejected.items())),
        "rejected_details": rejected_details,
        "sources": source_rows,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Audit HVNH knowledge quality without changing data")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--strict", action="store_true",
                        help="Fail for broken indexed data, failed versions or quarantined content")
    args = parser.parse_args()
    try:
        report = await collect()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        failed_versions = report["version_statuses"].get("FAILED", 0)
        broken = sum(report["integrity"].values())
        if args.strict and (failed_versions or broken or report["counts"]["quarantined"]):
            raise SystemExit(1)
    finally:
        await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
