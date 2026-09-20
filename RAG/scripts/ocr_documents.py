"""OCR scanned PDFs discovered by an approved crawler source."""
import argparse
import asyncio
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit
from uuid import UUID

from sqlalchemy import select

from app.db.session import AsyncSessionLocal, dispose_engine
from app.knowledge.crawler.extractors import ExtractedDocument
from app.knowledge.crawler.fetcher import SafeFetcher
from app.knowledge.crawler.versioning import save_web_version
from app.knowledge.ocr import get_ocr_provider
from app.knowledge.policy import assess_content, assess_url
from app.models.crawler import AICrawlItem, AICrawlRun, AISource, AISourceURL


async def main() -> None:
    parser = argparse.ArgumentParser(description="OCR rejected scanned PDFs from an approved crawl")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--run-id", type=UUID)
    scope.add_argument("--source-id", type=UUID)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--include-legacy", action="store_true",
                        help="Also retry PDFs previously labelled UnsupportedDocument")
    args = parser.parse_args()
    error_codes = ["OCR_REQUIRED"]
    if args.include_legacy:
        error_codes.append("UnsupportedDocument")
    async with AsyncSessionLocal() as session:
        query = (
            select(AICrawlItem, AISourceURL, AISource)
            .join(AICrawlRun, AICrawlRun.id == AICrawlItem.run_id)
            .join(AISource, AISource.id == AICrawlRun.source_id)
            .join(AISourceURL, AISourceURL.id == AICrawlItem.source_url_id)
            .where(AICrawlItem.status == "REJECTED", AICrawlItem.error_code.in_(error_codes))
        )
        if args.run_id:
            query = query.where(AICrawlItem.run_id == args.run_id).order_by(AICrawlItem.finished_at)
        else:
            query = (query.where(AISource.id == args.source_id)
                     .distinct(AISourceURL.id)
                     .order_by(AISourceURL.id, AICrawlItem.finished_at.desc()))
        query = query.limit(args.limit)
        rows = (await session.execute(query)).all()
    safe_rows = []
    excluded = 0
    for item, source_url, source in rows:
        decision = assess_url(source_url.canonical_url, source.metadata_)
        if decision.allowed:
            safe_rows.append((item, source_url, source))
            continue
        async with AsyncSessionLocal() as session:
            db_item = await session.get(AICrawlItem, item.id)
            db_item.error_code = "PII_EXCLUDED"
            db_item.metadata_ = {**dict(db_item.metadata_ or {}), "exclusion_reason": decision.reason}
            await session.commit()
        excluded += 1
        print(f"ocr_excluded reason={decision.reason} url={source_url.canonical_url}", flush=True)
    provider = get_ocr_provider() if safe_rows else None
    completed = failed = duplicates = 0
    for position, (item, source_url, source) in enumerate(safe_rows, 1):
        fetcher = SafeFetcher(list(source.allowed_domains), list(source.allowed_path_prefixes))
        try:
            print(f"ocr_start item={position}/{len(safe_rows)} url={source_url.canonical_url}", flush=True)
            fetched = await fetcher.fetch(source_url.canonical_url)
            result = await provider.extract_pdf(fetched.body)
            filename = unquote(PurePosixPath(urlsplit(fetched.url).path).name)
            content_policy = assess_content(filename, result.content, source.metadata_)
            if not content_policy.allowed:
                async with AsyncSessionLocal() as session:
                    db_item = await session.get(AICrawlItem, item.id)
                    db_item.error_code = content_policy.code
                    db_item.metadata_ = {**dict(db_item.metadata_ or {}),
                                         "exclusion_reason": content_policy.reason}
                    await session.commit()
                excluded += 1
                print(f"ocr_excluded reason={content_policy.reason} url={source_url.canonical_url}", flush=True)
                continue
            extracted = ExtractedDocument(
                title=filename, content=result.content, page_count=result.page_count,
                metadata={"page_ranges": result.page_ranges, "ocr_engine": result.engine, "ocr": True},
            )
            async with AsyncSessionLocal() as session:
                db_item = await session.get(AICrawlItem, item.id)
                db_source_url = await session.get(AISourceURL, source_url.id)
                db_source = await session.get(AISource, source.id)
                saved = await save_web_version(session, db_source, db_source_url, extracted, "application/pdf")
                db_item.status = "UNCHANGED" if saved.duplicate else "SAVED"
                db_item.error_code = None
                db_item.document_version_id = saved.version_id
                await session.commit()
                duplicates += int(saved.duplicate)
                completed += 1
                print(f"ocr_saved pages={result.page_count} duplicate={str(saved.duplicate).lower()} url={source_url.canonical_url}", flush=True)
        except Exception as exc:
            failed += 1
            print(f"ocr_failed url={source_url.canonical_url} error={type(exc).__name__}", flush=True)
        finally:
            await fetcher.close()
    await dispose_engine()
    print(f"ocr=complete selected={len(rows)} completed={completed} duplicates={duplicates} excluded={excluded} failed={failed}", flush=True)
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    asyncio.run(main())
