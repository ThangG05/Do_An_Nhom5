import asyncio
from collections import deque
from dataclasses import replace
from datetime import UTC, datetime
import logging
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from redis.exceptions import RedisError, TimeoutError as RedisTimeoutError
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.knowledge.crawler.extractors import OCRRequired, UnsupportedDocument, extract_document
from app.knowledge.crawler.fetcher import FetchError, SafeFetcher
from app.knowledge.crawler.queue import CrawlQueue
from app.knowledge.pipeline_queue import PipelineQueue
from app.knowledge.policy import assess_content, assess_url
from app.knowledge.quality import assess_extraction
from app.knowledge.crawler.security import UnsafeURL, canonicalize_url, is_in_scope, url_hash
from app.knowledge.crawler.versioning import save_web_version
from app.models.crawler import AICrawlItem, AICrawlRun, AISource, AISourceURL
from app.services.redis import get_redis_client

logger = logging.getLogger(__name__)


def _is_attachment_url(url: str) -> bool:
    return urlsplit(url).path.casefold().endswith((".pdf", ".docx", ".xlsx", ".csv", ".tsv", ".txt"))


def _rejection_code(exc: Exception) -> str:
    if isinstance(exc, OCRRequired):
        return "OCR_REQUIRED"
    return type(exc).__name__[:100]


def _should_store_page(source: AISource, url: str, content_type: str) -> bool:
    """Store files and explicitly recognised HTML detail pages, not category pages."""
    if content_type != "text/html":
        return True
    path = urlsplit(url).path.lower()
    if path.endswith((".html", ".htm")):
        return True
    configured = source.metadata_.get("html_detail_path_prefixes", []) if source.metadata_ else []
    return any(path.startswith(str(prefix).lower()) for prefix in configured)


def _resume_checkpoint(previous_run: AICrawlRun | None, fresh_start: bool) -> dict:
    if fresh_start or previous_run is None or previous_run.status != "PARTIAL":
        return {}
    checkpoint = dict(previous_run.metadata_ or {})
    return checkpoint if checkpoint.get("frontier") else {}


async def _known_url(session, source_id, url):
    digest = url_hash(url)
    row = await session.scalar(select(AISourceURL).where(AISourceURL.source_id == source_id, AISourceURL.url_hash == digest))
    if row is None:
        row = AISourceURL(source_id=source_id, canonical_url=url, url_hash=digest)
        session.add(row); await session.flush()
    return row


async def process_run(run_id) -> None:
    async with AsyncSessionLocal() as session:
        run = await session.get(AICrawlRun, run_id)
        if run is None or run.status not in {"PENDING", "QUEUED"}: return
        source = await session.get(AISource, run.source_id)
        if source is None or not source.enabled:
            run.status, run.error_code, run.finished_at = "FAILED", "SOURCE_DISABLED", datetime.now(UTC)
            await session.commit(); return
        run.status, run.started_at = "RUNNING", datetime.now(UTC); await session.commit()
        logger.info("crawl run started", extra={"run_id": str(run.id), "source_id": str(source.id)})
        source_id = source.id
        domains, paths = list(source.allowed_domains), list(source.allowed_path_prefixes)
        crawl_delay_seconds = source.crawl_delay_seconds
        max_pages_per_run = source.max_pages_per_run
        max_depth = source.max_depth
        fetcher = SafeFetcher(domains, paths)
        robots = None
        try:
            origin = urlsplit(source.base_url)
            robots_url = f"{origin.scheme}://{origin.netloc}/robots.txt"
            robots_result = await fetcher.fetch(robots_url, enforce_paths=False)
            robots = RobotFileParser(robots_url)
            robots.parse(robots_result.body.decode("utf-8", errors="replace").splitlines())
        except Exception:
            logger.warning("robots.txt unavailable", extra={"source_id": str(source.id)})
        fresh_start = bool((run.metadata_ or {}).get("fresh_start"))
        previous_run = await session.scalar(
            select(AICrawlRun).where(
                AICrawlRun.source_id == source.id,
                AICrawlRun.id != run.id,
            ).order_by(AICrawlRun.queued_at.desc()).limit(1)
        )
        checkpoint = _resume_checkpoint(previous_run, fresh_start)
        if checkpoint:
            pending = deque(
                (entry["url"], int(entry["depth"]), entry.get("parent"))
                for entry in checkpoint["frontier"]
            )
            seen = set(checkpoint.get("visited", []))
        else:
            pending, seen = deque([(source.base_url, 0, None)]), set()
        previous_attachment_audit = (checkpoint or {}).get("attachment_audit", {})
        queued = {entry[0] for entry in pending}
        attachment_candidates: set[str] = set()
        attachments_saved: set[str] = set()
        attachments_rejected: set[str] = set()
        processed_this_run = 0
        try:
            while pending and processed_this_run < max_pages_per_run:
                raw, depth, parent = pending.popleft()
                queued.discard(raw)
                try: url = canonicalize_url(raw, parent)
                except UnsafeURL: continue
                if url in seen or not is_in_scope(url, domains, paths): continue
                seen.add(url)
                processed_this_run += 1
                known = await _known_url(session, source.id, url)
                item = AICrawlItem(run_id=run.id, source_url_id=known.id, url=url, url_hash=known.url_hash,
                                   status="FETCHING", depth=depth, discovered_from=parent, started_at=datetime.now(UTC))
                session.add(item); run.pages_discovered = len(seen); await session.commit()
                if robots is not None and not robots.can_fetch(fetcher.settings.crawler_user_agent, url):
                    item.status, item.error_code, item.finished_at = "REJECTED", "ROBOTS_DENIED", datetime.now(UTC)
                    await session.commit(); continue
                url_policy = assess_url(url, source.metadata_)
                if not url_policy.allowed:
                    item.status, item.error_code, item.finished_at = "REJECTED", url_policy.code, datetime.now(UTC)
                    item.metadata_ = {"exclusion_reason": url_policy.reason}
                    run.items_failed += 1
                    await session.commit()
                    continue
                try:
                    fetched = await fetcher.fetch(
                        url,
                        None if fresh_start else known.etag,
                        None if fresh_start else known.last_modified,
                    )
                    now = datetime.now(UTC); known.last_checked_at = now; known.last_http_status = fetched.status_code
                    item.http_status = fetched.status_code; item.finished_at = now
                    if fetched.status_code == 304:
                        item.status = "UNCHANGED"; run.documents_unchanged += 1
                        if _is_attachment_url(fetched.url):
                            attachments_saved.add(fetched.url)
                        await session.commit(); continue
                    run.pages_fetched += 1; known.etag = fetched.etag; known.last_modified = fetched.last_modified
                    item.content_type = fetched.content_type; item.response_bytes = len(fetched.body)
                    # Short category pages can still contain useful discovery links.
                    extracted = extract_document(fetched.body, fetched.content_type, fetched.url, allow_short=True)
                    quality = assess_extraction(extracted, allow_short=not _should_store_page(
                        source, fetched.url, fetched.content_type
                    ))
                    if not quality.accepted:
                        item.status, item.error_code = "REJECTED", quality.code
                        item.metadata_ = {"quality": quality.metrics, "quality_score": quality.score}
                        run.items_failed += 1
                        await session.commit()
                        continue
                    extracted = replace(extracted, metadata={
                        **extracted.metadata,
                        "extraction_quality": {"score": quality.score, **quality.metrics},
                        "canonical_structure": {
                            "sections": len(extracted.sections), "tables": len(extracted.tables),
                        },
                    })
                    content_policy = assess_content(extracted.title, extracted.content, source.metadata_)
                    if not content_policy.allowed:
                        item.status, item.error_code, item.finished_at = "REJECTED", content_policy.code, datetime.now(UTC)
                        item.metadata_ = {"exclusion_reason": content_policy.reason}
                        run.items_failed += 1
                        await session.commit()
                        continue
                    attachment_candidates.update(link for link in extracted.links if _is_attachment_url(link))
                    item.status = "EXTRACTED"
                    if _should_store_page(source, fetched.url, fetched.content_type):
                        if len(extracted.content) < 40:
                            raise UnsupportedDocument("document has too little extractable text")
                        saved = await save_web_version(session, source, known, extracted, fetched.content_type,
                                                       discovered_from=parent)
                        item.document_version_id = saved.version_id; item.status = "UNCHANGED" if saved.duplicate else "SAVED"
                        if saved.duplicate: run.documents_unchanged += 1
                        else: run.documents_created += 1
                        if _is_attachment_url(fetched.url):
                            attachments_saved.add(fetched.url)
                    if depth < max_depth:
                        for link in extracted.links:
                            try: child = canonicalize_url(link, fetched.url)
                            except UnsafeURL: continue
                            if child not in seen and child not in queued and is_in_scope(child, domains, paths):
                                pending.append((child, depth + 1, fetched.url))
                                queued.add(child)
                    await session.commit()
                    logger.info("crawl page processed", extra={"run_id": str(run.id), "url": url,
                                                                "discovered": len(seen), "queued": len(pending)})
                except (FetchError, UnsupportedDocument, UnsafeURL, ValueError) as exc:
                    await session.rollback()
                    item = await session.scalar(select(AICrawlItem).where(
                        AICrawlItem.run_id == run_id,
                        AICrawlItem.url_hash == url_hash(url),
                    ))
                    if item: item.status, item.error_code, item.finished_at = "REJECTED", _rejection_code(exc), datetime.now(UTC)
                    if _is_attachment_url(url):
                        attachments_rejected.add(url)
                    run = await session.get(AICrawlRun, run_id); run.items_failed += 1; await session.commit()
                    source = await session.get(AISource, source_id)
                if crawl_delay_seconds:
                    await asyncio.sleep(crawl_delay_seconds)
            run = await session.get(AICrawlRun, run_id); source = await session.get(AISource, run.source_id); now = datetime.now(UTC)
            frontier = [
                {"url": raw, "depth": depth, "parent": parent}
                for raw, depth, parent in pending
            ]
            run.metadata_ = {
                **dict(run.metadata_ or {}),
                "frontier": frontier,
                "visited": sorted(seen),
                "attachment_audit": {
                    "discovered": int(previous_attachment_audit.get("discovered", 0)) + len(attachment_candidates),
                    "saved_or_unchanged": int(previous_attachment_audit.get("saved_or_unchanged", 0)) + len(attachments_saved),
                    "rejected": int(previous_attachment_audit.get("rejected", 0)) + len(attachments_rejected),
                    "pending_in_frontier": sum(_is_attachment_url(entry["url"]) for entry in frontier),
                },
            }
            run.status = "PARTIAL" if run.items_failed or frontier else "SUCCEEDED"; run.finished_at = now
            source.last_checked_at = source.last_success_at = now; source.consecutive_failures = 0; await session.commit()
            logger.info("crawl run finished", extra={"run_id": str(run.id), "status": run.status,
                                                       "fetched": run.pages_fetched,
                                                       "documents_created": run.documents_created,
                                                       "failed": run.items_failed})
        except Exception as exc:
            await session.rollback(); run = await session.get(AICrawlRun, run_id)
            source = await session.get(AISource, run.source_id) if run else None
            if run: run.status, run.error_code, run.finished_at = "FAILED", type(exc).__name__[:100], datetime.now(UTC)
            if source: source.consecutive_failures += 1; source.last_checked_at = datetime.now(UTC)
            await session.commit(); logger.exception("crawl run failed", extra={"run_id": str(run_id), "error_type": type(exc).__name__})
        finally: await fetcher.close()


async def run_worker() -> None:
    queue = CrawlQueue(get_redis_client())
    while True:
        try:
            message = await queue.consume()
        except RedisTimeoutError:
            # A blocking stream read timing out while idle is not an outage.
            continue
        except RedisError as exc:
            logger.warning("crawl queue temporarily unavailable", extra={"error_type": type(exc).__name__})
            await asyncio.sleep(2)
            continue
        if message is None: continue
        async with AsyncSessionLocal() as session:
            run = await session.get(AICrawlRun, message.run_id); source_id = run.source_id if run else None
        if source_id is None: await queue.acknowledge(message.message_id); continue
        token = await queue.acquire_source_lock(source_id)
        if token is None:
            # XREADGROUP with ">" will not redeliver this pending entry by itself.
            await queue.enqueue(message.run_id)
            await queue.acknowledge(message.message_id)
            await asyncio.sleep(1)
            continue
        try:
            await process_run(message.run_id)
            async with AsyncSessionLocal() as session:
                completed_run = await session.get(AICrawlRun, message.run_id)
                should_process = completed_run is not None and completed_run.status in {"SUCCEEDED", "PARTIAL"}
            if should_process:
                await PipelineQueue(get_redis_client()).enqueue(message.run_id)
            await queue.acknowledge(message.message_id)
        finally: await queue.release_source_lock(source_id, token)
