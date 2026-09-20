import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import exists, or_, select

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.knowledge.crawler.queue import CrawlQueue
from app.models.crawler import AICrawlRun, AISource
from app.services.redis import get_redis_client
async def _enqueue_due_sources() -> tuple[int, int]:
    """Enqueue overdue sources and explicitly resume their latest PARTIAL run.

    A new recovery run is used instead of reusing the terminal run. The worker
    reads the latest PARTIAL checkpoint, so frontier/visited state is retained
    while every execution remains auditable and idempotent.
    """
    now = datetime.now(UTC)
    run_ids = []
    partial_count = 0
    async with AsyncSessionLocal() as session:
        sources = (await session.scalars(select(AISource).where(
            AISource.enabled.is_(True),
            or_(AISource.next_crawl_at.is_(None), AISource.next_crawl_at <= now),
            ~exists().where(
                AICrawlRun.source_id == AISource.id,
                AICrawlRun.status.in_(("PENDING", "QUEUED", "RUNNING")),
            ),
        ).with_for_update(skip_locked=True))).all()
        for source in sources:
            latest_run = await session.scalar(select(AICrawlRun).where(
                AICrawlRun.source_id == source.id,
            ).order_by(AICrawlRun.queued_at.desc()).limit(1))
            if latest_run is not None and latest_run.status == "PARTIAL":
                trigger = "RECOVERY"
                metadata = {"resumed_partial_run_id": str(latest_run.id)}
                partial_count += 1
            else:
                trigger = "SCHEDULED"
                metadata = {}
            run = AICrawlRun(source_id=source.id, status="PENDING", trigger_type=trigger,
                             metadata_=metadata)
            session.add(run)
            source.next_crawl_at = now + timedelta(minutes=source.schedule_minutes)
            await session.flush()
            run_ids.append(run.id)
        await session.commit()
    queue = CrawlQueue(get_redis_client())
    for run_id in run_ids:
        await queue.enqueue(run_id)
        async with AsyncSessionLocal() as session:
            run = await session.get(AICrawlRun, run_id)
            if run and run.status == "PENDING": run.status = "QUEUED"; await session.commit()
    return len(run_ids), partial_count


async def enqueue_due_sources() -> int:
    total, _ = await _enqueue_due_sources()
    return total


async def recover_pending_runs() -> int:
    async with AsyncSessionLocal() as session:
        run_ids = list((await session.scalars(select(AICrawlRun.id).where(AICrawlRun.status == "PENDING"))).all())
    queue = CrawlQueue(get_redis_client())
    for run_id in run_ids:
        await queue.enqueue(run_id)
        async with AsyncSessionLocal() as session:
            run = await session.get(AICrawlRun, run_id)
            if run and run.status == "PENDING": run.status = "QUEUED"; await session.commit()
    return len(run_ids)


async def recover_stale_runs() -> int:
    """Replace abandoned queued/running runs without allowing their old queue message to execute."""
    settings = get_settings()
    now = datetime.now(UTC)
    cutoff = now - timedelta(minutes=settings.crawler_run_stale_minutes)
    recovery_ids = []
    async with AsyncSessionLocal() as session:
        stale = (await session.scalars(select(AICrawlRun).join(
            AISource, AISource.id == AICrawlRun.source_id
        ).where(
            AISource.enabled.is_(True),
            AICrawlRun.status.in_(("QUEUED", "RUNNING")),
            AICrawlRun.queued_at < cutoff,
        ).with_for_update(skip_locked=True))).all()
        for old in stale:
            old.status, old.finished_at, old.error_code = "FAILED", now, "STALE_RUN_RECOVERED"
            recovery = AICrawlRun(source_id=old.source_id, status="PENDING", trigger_type="RECOVERY",
                                  metadata_={"recovered_run_id": str(old.id)})
            session.add(recovery)
            await session.flush()
            recovery_ids.append(recovery.id)
        await session.commit()
    queue = CrawlQueue(get_redis_client())
    for run_id in recovery_ids:
        await queue.enqueue(run_id)
        async with AsyncSessionLocal() as session:
            run = await session.get(AICrawlRun, run_id)
            if run and run.status == "PENDING":
                run.status = "QUEUED"
                await session.commit()
    return len(recovery_ids)


async def recover_incomplete_runs() -> tuple[int, int]:
    """Retry recent PARTIAL/FAILED sources with bounded, persisted attempts."""
    settings = get_settings()
    if settings.crawler_recovery_max_attempts == 0:
        return 0, 0
    now = datetime.now(UTC)
    cutoff = now - timedelta(minutes=settings.crawler_recovery_retry_minutes)
    recovery_ids: list = []
    partial_count = failed_count = 0
    async with AsyncSessionLocal() as session:
        sources = (await session.scalars(select(AISource).where(
            AISource.enabled.is_(True),
            ~exists().where(
                AICrawlRun.source_id == AISource.id,
                AICrawlRun.status.in_(("PENDING", "QUEUED", "RUNNING")),
            ),
        ).with_for_update(skip_locked=True))).all()
        for source in sources:
            latest = await session.scalar(select(AICrawlRun).where(
                AICrawlRun.source_id == source.id,
            ).order_by(AICrawlRun.queued_at.desc()).limit(1))
            if latest is None or latest.status not in {"PARTIAL", "FAILED"}:
                continue
            if latest.finished_at is None or latest.finished_at > cutoff:
                continue
            previous_attempt = int((latest.metadata_ or {}).get("scheduler_recovery_attempt", 0))
            if previous_attempt >= settings.crawler_recovery_max_attempts:
                continue
            metadata = {
                "scheduler_recovery_attempt": previous_attempt + 1,
                ("resumed_partial_run_id" if latest.status == "PARTIAL" else "recovered_failed_run_id"): str(latest.id),
            }
            recovery = AICrawlRun(source_id=source.id, status="PENDING", trigger_type="RECOVERY",
                                  metadata_=metadata)
            session.add(recovery)
            await session.flush()
            recovery_ids.append(recovery.id)
            if latest.status == "PARTIAL":
                partial_count += 1
            else:
                failed_count += 1
        await session.commit()
    queue = CrawlQueue(get_redis_client())
    for run_id in recovery_ids:
        await queue.enqueue(run_id)
        async with AsyncSessionLocal() as session:
            run = await session.get(AICrawlRun, run_id)
            if run and run.status == "PENDING":
                run.status = "QUEUED"
                await session.commit()
    return partial_count, failed_count


async def scheduler_once() -> dict[str, int]:
    stale = await recover_stale_runs()
    pending = await recover_pending_runs()
    partial_retry, failed_retry = await recover_incomplete_runs()
    due, partial = await _enqueue_due_sources()
    return {"stale_recovered": stale, "pending_requeued": pending,
            "due_enqueued": due, "partial_enqueued": partial,
            "partial_retried": partial_retry, "failed_retried": failed_retry}


async def run_scheduler() -> None:
    settings = get_settings()
    while True:
        await scheduler_once()
        await asyncio.sleep(settings.crawler_scheduler_poll_seconds)
