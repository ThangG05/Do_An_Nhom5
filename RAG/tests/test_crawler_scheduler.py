from datetime import UTC, datetime, timedelta

from app.knowledge.crawler.scheduler import _next_automatic_crawl_at
from app.models.crawler import AICrawlRun, AISource


def test_old_source_with_short_schedule_is_limited_to_one_crawl_per_day() -> None:
    now = datetime.now(UTC)
    source = AISource(schedule_minutes=15, next_crawl_at=now - timedelta(hours=1))
    latest = AICrawlRun(queued_at=now - timedelta(hours=2))
    assert _next_automatic_crawl_at(source, latest) == latest.queued_at + timedelta(days=1)


def test_longer_source_schedule_and_first_run_are_preserved() -> None:
    now = datetime.now(UTC)
    source = AISource(schedule_minutes=2880, next_crawl_at=now + timedelta(days=3))
    latest = AICrawlRun(queued_at=now)
    assert _next_automatic_crawl_at(source, latest) == source.next_crawl_at
    assert _next_automatic_crawl_at(source, None) == source.next_crawl_at
