from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AIDocumentType


class AISource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_sources"
    name: Mapped[str] = mapped_column(String(255))
    base_url: Mapped[str] = mapped_column(Text, unique=True)
    allowed_domains: Mapped[list[str]] = mapped_column(JSONB, default=list)
    allowed_path_prefixes: Mapped[list[str]] = mapped_column(JSONB, default=list)
    document_type: Mapped[AIDocumentType] = mapped_column(
        Enum(AIDocumentType, name="ai_document_type"), default=AIDocumentType.OTHER
    )
    issuer: Mapped[str | None] = mapped_column(String(255))
    academic_year: Mapped[str | None] = mapped_column(String(9))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    schedule_minutes: Mapped[int] = mapped_column(Integer, default=1440)
    max_depth: Mapped[int] = mapped_column(Integer, default=3)
    max_pages_per_run: Mapped[int] = mapped_column(Integer, default=100)
    crawl_delay_seconds: Mapped[float] = mapped_column(default=1.0)
    next_crawl_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    __table_args__ = (
        CheckConstraint("schedule_minutes >= 15", name="ai_source_schedule"),
        CheckConstraint("max_depth BETWEEN 0 AND 10", name="ai_source_depth"),
        CheckConstraint("max_pages_per_run BETWEEN 1 AND 5000", name="ai_source_page_limit"),
        CheckConstraint("crawl_delay_seconds >= 0", name="ai_source_delay"),
        Index("idx_ai_sources_due", "enabled", "next_crawl_at"),
    )


class AISourceURL(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_source_urls"
    source_id: Mapped[UUID] = mapped_column(ForeignKey("ai_sources.id", ondelete="CASCADE"))
    canonical_url: Mapped[str] = mapped_column(Text)
    url_hash: Mapped[str] = mapped_column(String(64))
    etag: Mapped[str | None] = mapped_column(Text)
    last_modified: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    last_http_status: Mapped[int | None]
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("ai_documents.id", ondelete="SET NULL"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("source_id", "url_hash", name="uq_ai_source_url_hash"),
        Index("idx_ai_source_urls_source", "source_id", "last_checked_at"),
        Index("idx_ai_source_urls_document", "document_id"),
    )


class AICrawlRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_crawl_runs"
    source_id: Mapped[UUID] = mapped_column(ForeignKey("ai_sources.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    trigger_type: Mapped[str] = mapped_column(String(20), default="SCHEDULED")
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0)
    pages_fetched: Mapped[int] = mapped_column(Integer, default=0)
    documents_created: Mapped[int] = mapped_column(Integer, default=0)
    documents_unchanged: Mapped[int] = mapped_column(Integer, default=0)
    items_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(100))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','QUEUED','RUNNING','SUCCEEDED','PARTIAL','FAILED','CANCELLED')", name="ai_crawl_run_status"),
        CheckConstraint("trigger_type IN ('SCHEDULED','MANUAL','RECOVERY')", name="ai_crawl_trigger"),
        Index("idx_ai_crawl_runs_source", "source_id", text("queued_at DESC")),
        Index("idx_ai_crawl_runs_status", "status", "queued_at"),
    )


class AICrawlItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_crawl_items"
    run_id: Mapped[UUID] = mapped_column(ForeignKey("ai_crawl_runs.id", ondelete="CASCADE"))
    source_url_id: Mapped[UUID | None] = mapped_column(ForeignKey("ai_source_urls.id", ondelete="SET NULL"))
    url: Mapped[str] = mapped_column(Text)
    url_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="DISCOVERED")
    depth: Mapped[int] = mapped_column(Integer)
    discovered_from: Mapped[str | None] = mapped_column(Text)
    http_status: Mapped[int | None]
    content_type: Mapped[str | None] = mapped_column(String(255))
    response_bytes: Mapped[int | None]
    document_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("ai_document_versions.id", ondelete="SET NULL"))
    error_code: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("run_id", "url_hash", name="uq_ai_crawl_item_url"),
        CheckConstraint("status IN ('DISCOVERED','FETCHING','UNCHANGED','DOWNLOADED','EXTRACTED','SAVED','REJECTED','FAILED')", name="ai_crawl_item_status"),
        CheckConstraint("depth >= 0", name="ai_crawl_item_depth"),
        Index("idx_ai_crawl_items_run", "run_id", "status"),
    )
