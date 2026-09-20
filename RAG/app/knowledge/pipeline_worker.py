"""Orchestrate post-crawl OCR and indexing outside the crawler process."""
import asyncio
from datetime import UTC, datetime
import logging
from pathlib import Path
import re
import sys
from uuid import UUID

from redis.exceptions import RedisError, TimeoutError as RedisTimeoutError
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.knowledge.pipeline_queue import PipelineQueue
from app.models.crawler import AICrawlRun, AISourceURL
from app.models.enums import AIDocumentStatus
from app.models.rag import AIDocumentVersion
from app.services.redis import get_redis_client

logger = logging.getLogger(__name__)
RAG_ROOT = Path(__file__).resolve().parents[2]


class PipelineStageError(RuntimeError):
    """A post-crawl stage failed and the queue message may be retried."""


def next_pipeline_failure(attempts: int, max_retries: int) -> tuple[int, str]:
    next_attempt = attempts + 1
    return next_attempt, "RETRYING" if next_attempt <= max_retries else "FAILED"


async def _run_module(*arguments: str) -> int:
    settings = get_settings()
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", *arguments,
        cwd=str(RAG_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        output, _ = await asyncio.wait_for(
            process.communicate(), timeout=settings.pipeline_stage_timeout_seconds
        )
    except TimeoutError:
        process.kill()
        await process.communicate()
        logger.error("pipeline stage timed out", extra={"stage": arguments[0]})
        return 124
    logger.info("pipeline stage finished", extra={
        "stage": arguments[0], "exit_code": process.returncode,
        "output_bytes": len(output or b""),
        "diagnostic": _safe_stage_diagnostic(output),
    })
    return int(process.returncode or 0)


def _safe_stage_diagnostic(output: bytes | None) -> str | None:
    """Expose only aggregate stage summaries, never document text or URLs."""
    lines = (output or b"").decode("utf-8", errors="replace").splitlines()
    allowed = re.compile(r"^(pipeline=complete|index_error_types=|ocr=complete|references=)")
    selected = [line[:500] for line in lines if allowed.match(line)]
    return " | ".join(selected[-3:]) or None


async def process_pipeline_run(run_id: UUID) -> bool:
    async with AsyncSessionLocal() as session:
        run = await session.get(AICrawlRun, run_id)
        if run is None:
            return False
        source_id = run.source_id
        metadata = dict(run.metadata_ or {})
        pipeline = dict(metadata.get("pipeline") or {})
        if pipeline.get("status") == "SUCCEEDED":
            return True
        pipeline.update({"status": "PROCESSING", "started_at": datetime.now(UTC).isoformat()})
        metadata["pipeline"] = pipeline
        run.metadata_ = metadata
        await session.commit()

    ocr_exit = await _run_module("scripts.ocr_documents", "--run-id", str(run_id))
    index_exit = await _run_module("scripts.process_source", "--source-id", str(source_id), "--limit", "1000")
    succeeded = ocr_exit == 0 and index_exit == 0
    async with AsyncSessionLocal() as session:
        run = await session.get(AICrawlRun, run_id)
        if run:
            metadata = dict(run.metadata_ or {})
            previous = dict(metadata.get("pipeline") or {})
            metadata["pipeline"] = {
                **previous,
                "status": "SUCCEEDED" if succeeded else "PARTIAL",
                "ocr_exit_code": ocr_exit,
                "index_exit_code": index_exit,
                "finished_at": datetime.now(UTC).isoformat(),
            }
            run.metadata_ = metadata
            await session.commit()
    return succeeded


async def recover_incomplete_sources(queue: PipelineQueue) -> int:
    """Requeue one latest completed crawl run per source with unfinished versions.

    This closes the gap left by Redis consumer messages that were acknowledged or
    stranded before a worker restart. Processing is idempotent at version level.
    """
    async with AsyncSessionLocal() as session:
        source_ids = list((await session.scalars(
            select(AISourceURL.source_id)
            .join(AIDocumentVersion, AIDocumentVersion.document_id == AISourceURL.document_id)
            .where(AIDocumentVersion.status.in_((
                AIDocumentStatus.PENDING, AIDocumentStatus.PROCESSING,
            )))
            .distinct()
        )).all())
        run_ids: list[UUID] = []
        for source_id in source_ids:
            run = await session.scalar(
                select(AICrawlRun).where(
                    AICrawlRun.source_id == source_id,
                    AICrawlRun.status.in_(("SUCCEEDED", "PARTIAL")),
                ).order_by(AICrawlRun.queued_at.desc()).limit(1)
            )
            if run is None:
                continue
            metadata = dict(run.metadata_ or {})
            pipeline = dict(metadata.get("pipeline") or {})
            pipeline.update({
                "status": "QUEUED",
                "attempts": 0,
                "recovered_at": datetime.now(UTC).isoformat(),
            })
            metadata["pipeline"] = pipeline
            run.metadata_ = metadata
            run_ids.append(run.id)
        await session.commit()
    for run_id in run_ids:
        await queue.enqueue(run_id)
    if run_ids:
        logger.info("incomplete pipeline sources requeued", extra={"count": len(run_ids)})
    return len(run_ids)


async def run_pipeline_worker() -> None:
    queue = PipelineQueue(get_redis_client())
    while True:
        try:
            await recover_incomplete_sources(queue)
            break
        except RedisError as exc:
            logger.warning("pipeline recovery queue unavailable", extra={"error_type": type(exc).__name__})
            await asyncio.sleep(2)
    while True:
        try:
            message = await queue.consume()
        except RedisTimeoutError:
            # Upstash may close an idle blocking read at its socket deadline.
            continue
        except RedisError as exc:
            logger.warning("pipeline queue temporarily unavailable", extra={"error_type": type(exc).__name__})
            await asyncio.sleep(2)
            continue
        if message is None:
            continue
        async with AsyncSessionLocal() as session:
            run = await session.get(AICrawlRun, message.run_id)
            source_id = run.source_id if run else None
        if source_id is None:
            await queue.acknowledge(message.message_id)
            continue
        token = await queue.acquire_source_lock(source_id)
        if token is None:
            await queue.enqueue(message.run_id)
            await queue.acknowledge(message.message_id)
            await asyncio.sleep(1)
            continue
        try:
            try:
                succeeded = await process_pipeline_run(message.run_id)
                if not succeeded:
                    raise PipelineStageError("one or more pipeline stages failed")
            except Exception as exc:
                attempts = 1
                logger.exception("pipeline run failed", extra={"run_id": str(message.run_id),
                                                               "error_type": type(exc).__name__})
                async with AsyncSessionLocal() as session:
                    run = await session.get(AICrawlRun, message.run_id)
                    metadata = dict(run.metadata_ or {}) if run else {}
                    pipeline = dict(metadata.get("pipeline") or {})
                    settings = get_settings()
                    attempts, failure_status = next_pipeline_failure(
                        int(pipeline.get("attempts", 0)), settings.pipeline_max_retries
                    )
                    pipeline.update({"status": failure_status,
                                     "attempts": attempts, "error_type": type(exc).__name__})
                    metadata["pipeline"] = pipeline
                    if run:
                        run.metadata_ = metadata
                        await session.commit()
                if attempts <= settings.pipeline_max_retries:
                    await asyncio.sleep(settings.pipeline_retry_base_seconds * (2 ** (attempts - 1)))
                    await queue.enqueue(message.run_id)
            await queue.acknowledge(message.message_id)
        finally:
            await queue.release_source_lock(source_id, token)
