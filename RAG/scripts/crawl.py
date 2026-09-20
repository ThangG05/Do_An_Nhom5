import argparse
import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from urllib.parse import urlsplit
from uuid import UUID
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.knowledge.crawler.queue import CrawlQueue
from app.knowledge.crawler.security import canonicalize_url, is_in_scope, url_hash
from app.knowledge.crawler.metadata import infer_metadata
from app.knowledge.crawler.extractors import extract_document
from app.knowledge.crawler.fetcher import SafeFetcher
from app.knowledge.crawler.versioning import save_web_version
from app.knowledge.policy import assess_content, assess_url
from app.models.crawler import AICrawlItem, AICrawlRun, AISource, AISourceURL
from app.models.enums import AIDocumentStatus, AIDocumentType
from app.models.rag import AIDocument, AIDocumentVersion
from app.services.redis import close_redis, get_redis_client


async def add_source(args) -> None:
    base_url = canonicalize_url(args.url)
    domains = [x.strip().lower() for x in args.domains.split(",") if x.strip()]
    paths = [x.strip() for x in args.paths.split(",") if x.strip()]
    if not domains or not is_in_scope(base_url, domains, paths):
        raise ValueError("seed URL must be inside the approved scope")
    async with AsyncSessionLocal() as session:
        detail_paths = [x.strip() for x in args.detail_paths.split(",") if x.strip()]
        source_metadata = {"html_detail_path_prefixes": detail_paths}
        if args.document_code:
            source_metadata["document_code"] = args.document_code
        source_metadata["exclude_url_patterns"] = [x.strip() for x in args.exclude_url_patterns.split(",") if x.strip()]
        source_metadata["exclude_content_patterns"] = [x.strip() for x in args.exclude_content_patterns.split(",") if x.strip()]
        source = AISource(name=args.name, base_url=base_url, allowed_domains=domains,
                          allowed_path_prefixes=paths, document_type=AIDocumentType(args.type),
                          schedule_minutes=args.interval, max_depth=args.depth,
                          max_pages_per_run=args.max_pages, next_crawl_at=datetime.now(UTC),
                          metadata_=source_metadata)
        session.add(source); await session.commit(); print(f"source_id={source.id}")


async def enqueue(args) -> None:
    async with AsyncSessionLocal() as session:
        source = await session.get(AISource, UUID(args.source_id))
        if source is None: raise ValueError("source not found")
        run = await session.scalar(select(AICrawlRun).where(
            AICrawlRun.source_id == source.id, AICrawlRun.status == "PENDING"
        ).order_by(AICrawlRun.queued_at).limit(1))
        if run is None:
            run = AICrawlRun(source_id=source.id, status="PENDING", trigger_type="MANUAL",
                             metadata_={"fresh_start": bool(args.fresh)})
            session.add(run)
        elif args.fresh:
            run.metadata_ = {**dict(run.metadata_ or {}), "fresh_start": True}
        await session.commit()
    await CrawlQueue(get_redis_client()).enqueue(run.id)
    async with AsyncSessionLocal() as session:
        queued = await session.get(AICrawlRun, run.id); queued.status = "QUEUED"; await session.commit()
    await close_redis()
    print(f"run_id={run.id}")


async def run_now(args) -> None:
    """Run one crawl synchronously for maintenance and CI diagnostics."""
    source_id = UUID(args.source_id)
    async with AsyncSessionLocal() as session:
        source = await session.get(AISource, source_id)
        if source is None:
            raise ValueError("source not found")
        run = AICrawlRun(source_id=source.id, status="PENDING", trigger_type="MANUAL",
                         metadata_={"fresh_start": bool(args.fresh)})
        session.add(run)
        await session.commit()
        run_id = run.id
    from app.knowledge.crawler.worker import process_run
    await process_run(run_id)
    await show_run(SimpleNamespace(run_id=str(run_id)))


async def ingest_url(args) -> None:
    """Fetch one approved URL without expanding links, useful for targeted repairs."""
    source_id = UUID(args.source_id)
    async with AsyncSessionLocal() as session:
        source = await session.get(AISource, source_id)
        if source is None:
            raise ValueError("source not found")
        url = canonicalize_url(args.url)
        if not is_in_scope(url, list(source.allowed_domains), list(source.allowed_path_prefixes)):
            raise ValueError("URL is outside the approved source scope")
        decision = assess_url(url, source.metadata_)
        if not decision.allowed:
            raise ValueError(decision.code or "URL rejected by policy")
        fetcher = SafeFetcher(list(source.allowed_domains), list(source.allowed_path_prefixes))
        try:
            fetched = await fetcher.fetch(url)
            extracted = extract_document(fetched.body, fetched.content_type, fetched.url)
            content_decision = assess_content(extracted.title, extracted.content, source.metadata_)
            if not content_decision.allowed:
                raise ValueError(content_decision.code or "content rejected by policy")
            digest = url_hash(url)
            known = await session.scalar(select(AISourceURL).where(
                AISourceURL.source_id == source.id, AISourceURL.url_hash == digest))
            if known is None:
                known = AISourceURL(source_id=source.id, canonical_url=url, url_hash=digest)
                session.add(known)
                await session.flush()
            saved = await save_web_version(session, source, known, extracted, fetched.content_type)
            await session.commit()
            print(f"url={url} version_id={saved.version_id} duplicate={str(saved.duplicate).lower()}")
        finally:
            await fetcher.close()


async def list_sources(_) -> None:
    async with AsyncSessionLocal() as session:
        for source in (await session.scalars(select(AISource).order_by(AISource.name))).all():
            print(source.id, source.enabled, source.base_url)


async def set_enabled(args) -> None:
    async with AsyncSessionLocal() as session:
        source = await session.get(AISource, UUID(args.source_id))
        if source is None:
            raise ValueError("source not found")
        source.enabled = args.enabled == "true"
        await session.commit()
        print(f"source_id={source.id} enabled={str(source.enabled).lower()}")


async def find_url(args) -> None:
    url = canonicalize_url(args.url)
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(AISourceURL, AISource, AIDocumentVersion)
            .join(AISource, AISource.id == AISourceURL.source_id)
            .outerjoin(AIDocumentVersion, AIDocumentVersion.document_id == AISourceURL.document_id)
            .where(AISourceURL.url_hash == url_hash(url))
            .order_by(AIDocumentVersion.version_number.desc().nullslast())
        )).all()
        if not rows:
            print(f"found=false url={url}")
            return
        for source_url, source, version in rows:
            print(
                f"found=true source_id={source.id} document_id={source_url.document_id or '-'} "
                f"version_id={version.id if version else '-'} status={version.status.value if version else '-'} "
                f"url={source_url.canonical_url}"
            )


async def update_source(args) -> None:
    base_url = canonicalize_url(args.url)
    domains = [x.strip().lower() for x in args.domains.split(",") if x.strip()]
    paths = [x.strip() for x in args.paths.split(",") if x.strip()]
    if not domains or not is_in_scope(base_url, domains, paths):
        raise ValueError("seed URL must be inside the approved scope")
    async with AsyncSessionLocal() as session:
        source = await session.get(AISource, UUID(args.source_id))
        if source is None: raise ValueError("source not found")
        source.base_url = base_url
        source.allowed_domains = domains
        source.allowed_path_prefixes = paths
        if args.depth is not None:
            source.max_depth = args.depth
        if args.max_pages is not None:
            source.max_pages_per_run = args.max_pages
        if args.delay is not None:
            source.crawl_delay_seconds = args.delay
        if args.detail_paths is not None:
            metadata = dict(source.metadata_ or {})
            metadata["html_detail_path_prefixes"] = [
                x.strip() for x in args.detail_paths.split(",") if x.strip()
            ]
            source.metadata_ = metadata
        if args.exclude_url_patterns is not None or args.exclude_content_patterns is not None:
            metadata = dict(source.metadata_ or {})
            if args.exclude_url_patterns is not None:
                metadata["exclude_url_patterns"] = [
                    x.strip() for x in args.exclude_url_patterns.split(",") if x.strip()
                ]
            if args.exclude_content_patterns is not None:
                metadata["exclude_content_patterns"] = [
                    x.strip() for x in args.exclude_content_patterns.split(",") if x.strip()
                ]
            source.metadata_ = metadata
        await session.commit()
        print(f"source_id={source.id} url={source.base_url}")


async def show_run(args) -> None:
    async with AsyncSessionLocal() as session:
        run = await session.get(AICrawlRun, UUID(args.run_id))
        if run is None: raise ValueError("run not found")
        print(
            f"run_id={run.id} status={run.status} discovered={run.pages_discovered} "
            f"fetched={run.pages_fetched} created={run.documents_created} "
            f"unchanged={run.documents_unchanged} failed={run.items_failed} "
            f"error={run.error_code or '-'}"
        )
        audit = (run.metadata_ or {}).get("attachment_audit", {})
        if audit:
            print(
                "attachments "
                f"discovered={audit.get('discovered', 0)} "
                f"saved_or_unchanged={audit.get('saved_or_unchanged', 0)} "
                f"rejected={audit.get('rejected', 0)} "
                f"pending={audit.get('pending_in_frontier', 0)}"
            )
        pipeline = (run.metadata_ or {}).get("pipeline", {})
        if pipeline:
            print(
                f"pipeline status={pipeline.get('status', '-')} "
                f"attempts={pipeline.get('attempts', 0)} "
                f"ocr_exit={pipeline.get('ocr_exit_code', '-')} "
                f"index_exit={pipeline.get('index_exit_code', '-')}"
            )
        rejected = (await session.scalars(
            select(AICrawlItem).where(
                AICrawlItem.run_id == run.id,
                AICrawlItem.status == "REJECTED",
            ).order_by(AICrawlItem.url)
        )).all()
        for item in rejected:
            if item.url.lower().split("?", 1)[0].endswith((".pdf", ".docx", ".xlsx", ".csv", ".tsv", ".txt")):
                print(f"rejected_attachment error={item.error_code or '-'} url={item.url}")


async def cancel_run(args) -> None:
    async with AsyncSessionLocal() as session:
        run = await session.get(AICrawlRun, UUID(args.run_id))
        if run is None:
            raise ValueError("run not found")
        if run.status not in {"SUCCEEDED", "PARTIAL", "FAILED", "CANCELLED"}:
            run.status = "CANCELLED"
            run.finished_at = datetime.now(UTC)
            run.error_code = "MANUAL_CANCEL"
            await session.commit()
        print(f"run_id={run.id} status={run.status}")


async def normalize_source(args) -> None:
    source_id = UUID(args.source_id)
    async with AsyncSessionLocal() as session:
        source = await session.get(AISource, source_id)
        if source is None: raise ValueError("source not found")
        rows = (await session.execute(
            select(AIDocument, AIDocumentVersion, AISourceURL)
            .join(AISourceURL, AISourceURL.document_id == AIDocument.id)
            .join(AIDocumentVersion, AIDocumentVersion.document_id == AIDocument.id)
            .where(AISourceURL.source_id == source_id)
            .order_by(AIDocumentVersion.version_number)
        )).all()
        documents = set()
        for document, version, source_url in rows:
            inferred = infer_metadata(document.title, version.raw_content or "")
            document.document_type = source.document_type if source.document_type.value != "OTHER" else inferred.document_type
            document.academic_year = source.academic_year or inferred.academic_year
            document.published_at = inferred.published_at
            document.issuer = document.issuer or source.issuer or "Học viện Ngân hàng"
            metadata = dict(document.metadata_ or {})
            configured_details = [str(prefix).lower() for prefix in
                                  (source.metadata_ or {}).get("html_detail_path_prefixes", [])]
            path = urlsplit(source_url.canonical_url).path.lower()
            base_is_detail = any(path.startswith(prefix) for prefix in configured_details)
            metadata["retrieval_excluded"] = (
                source_url.canonical_url.rstrip("/") == source.base_url.rstrip("/")
                and not base_is_detail
            )
            document.metadata_ = metadata
            version_metadata = dict(version.metadata_ or {})
            if (not metadata["retrieval_excluded"]
                    and version.status.value == "ARCHIVED"
                    and version_metadata.get("chunk_skip_reason") == "retrieval_excluded"):
                version_metadata.pop("chunk_skip_reason", None)
                version.metadata_ = version_metadata
                version.status = AIDocumentStatus.PENDING
            documents.add(document.id)
        await session.commit()
        print(f"normalized={len(documents)}")


def make_parser():
    root = argparse.ArgumentParser(description="Manage approved crawl sources")
    commands = root.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add-source")
    add.add_argument("--name", required=True); add.add_argument("--url", required=True)
    add.add_argument("--domains", required=True); add.add_argument("--paths", default="")
    add.add_argument("--detail-paths", default="", help="Comma-separated HTML detail URL path prefixes")
    add.add_argument("--document-code", default=None,
                     help="Curated official document number for a single-document seed")
    add.add_argument("--exclude-url-patterns", default="", help="Comma-separated source policy patterns")
    add.add_argument("--exclude-content-patterns", default="", help="Comma-separated source policy patterns")
    add.add_argument("--type", choices=[x.value for x in AIDocumentType], default="OTHER")
    add.add_argument("--interval", type=int, default=1440); add.add_argument("--depth", type=int, default=2)
    add.add_argument("--max-pages", type=int, default=100); add.set_defaults(handler=add_source)
    manual = commands.add_parser("enqueue"); manual.add_argument("--source-id", required=True)
    manual.add_argument("--fresh", action="store_true", help="Ignore an older PARTIAL checkpoint and rescan from the seed URL")
    manual.set_defaults(handler=enqueue)
    direct = commands.add_parser("run-now")
    direct.add_argument("--source-id", required=True)
    direct.add_argument("--fresh", action="store_true")
    direct.set_defaults(handler=run_now)
    one = commands.add_parser("ingest-url")
    one.add_argument("--source-id", required=True)
    one.add_argument("--url", required=True)
    one.set_defaults(handler=ingest_url)
    update = commands.add_parser("update-source"); update.add_argument("--source-id", required=True)
    update.add_argument("--url", required=True); update.add_argument("--domains", required=True)
    update.add_argument("--paths", default="")
    update.add_argument("--detail-paths", default=None, help="Comma-separated HTML detail URL path prefixes")
    update.add_argument("--exclude-url-patterns", default=None)
    update.add_argument("--exclude-content-patterns", default=None)
    update.add_argument("--depth", type=int, default=None)
    update.add_argument("--max-pages", type=int, default=None)
    update.add_argument("--delay", type=float, default=None)
    update.set_defaults(handler=update_source)
    listing = commands.add_parser("list"); listing.set_defaults(handler=list_sources)
    enabled = commands.add_parser("set-enabled")
    enabled.add_argument("--source-id", required=True)
    enabled.add_argument("--enabled", choices=["true", "false"], required=True)
    enabled.set_defaults(handler=set_enabled)
    lookup = commands.add_parser("find-url")
    lookup.add_argument("--url", required=True); lookup.set_defaults(handler=find_url)
    status = commands.add_parser("status"); status.add_argument("--run-id", required=True); status.set_defaults(handler=show_run)
    cancel = commands.add_parser("cancel-run"); cancel.add_argument("--run-id", required=True); cancel.set_defaults(handler=cancel_run)
    normalize = commands.add_parser("normalize-source"); normalize.add_argument("--source-id", required=True); normalize.set_defaults(handler=normalize_source)
    return root


if __name__ == "__main__":
    parsed = make_parser().parse_args(); asyncio.run(parsed.handler(parsed))
