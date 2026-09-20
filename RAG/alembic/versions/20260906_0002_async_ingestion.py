"""Add asynchronous ingestion source registry and crawl tracking.

Revision ID: 20260906_0002
Revises: 20260903_0001
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260906_0002"
down_revision: str | None = "20260903_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

document_type = postgresql.ENUM(
    "REGULATION", "ANNOUNCEMENT", "FAQ", "GUIDE", "DECISION", "OTHER",
    name="ai_document_type", create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "ai_sources",
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("allowed_domains", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("allowed_path_prefixes", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("document_type", document_type, server_default="OTHER", nullable=False),
        sa.Column("issuer", sa.String(255)), sa.Column("academic_year", sa.String(9)),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("schedule_minutes", sa.Integer(), server_default="1440", nullable=False),
        sa.Column("max_depth", sa.Integer(), server_default="3", nullable=False),
        sa.Column("max_pages_per_run", sa.Integer(), server_default="100", nullable=False),
        sa.Column("crawl_delay_seconds", sa.Float(), server_default="1", nullable=False),
        sa.Column("next_crawl_at", sa.DateTime(timezone=True)),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("consecutive_failures", sa.Integer(), server_default="0", nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("schedule_minutes >= 15", name="ck_ai_sources_ai_source_schedule"),
        sa.CheckConstraint("max_depth BETWEEN 0 AND 10", name="ck_ai_sources_ai_source_depth"),
        sa.CheckConstraint("max_pages_per_run BETWEEN 1 AND 5000", name="ck_ai_sources_ai_source_page_limit"),
        sa.CheckConstraint("crawl_delay_seconds >= 0", name="ck_ai_sources_ai_source_delay"),
        sa.PrimaryKeyConstraint("id", name="pk_ai_sources"),
        sa.UniqueConstraint("base_url", name="uq_ai_sources_base_url"),
    )
    op.create_index("idx_ai_sources_due", "ai_sources", ["enabled", "next_crawl_at"])
    op.create_table(
        "ai_source_urls",
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False), sa.Column("url_hash", sa.String(64), nullable=False),
        sa.Column("etag", sa.Text()), sa.Column("last_modified", sa.Text()),
        sa.Column("content_hash", sa.String(64)), sa.Column("last_http_status", sa.Integer()),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)), sa.Column("last_changed_at", sa.DateTime(timezone=True)),
        sa.Column("document_id", postgresql.UUID(as_uuid=True)),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["ai_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["ai_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_ai_source_urls"),
        sa.UniqueConstraint("source_id", "url_hash", name="uq_ai_source_url_hash"),
    )
    op.create_index("idx_ai_source_urls_source", "ai_source_urls", ["source_id", "last_checked_at"])
    op.create_index("idx_ai_source_urls_document", "ai_source_urls", ["document_id"])
    op.create_table(
        "ai_crawl_runs",
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("trigger_type", sa.String(20), server_default="SCHEDULED", nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("pages_discovered", sa.Integer(), server_default="0", nullable=False),
        sa.Column("pages_fetched", sa.Integer(), server_default="0", nullable=False),
        sa.Column("documents_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("documents_unchanged", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_failed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_code", sa.String(100)),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("status IN ('PENDING','QUEUED','RUNNING','SUCCEEDED','PARTIAL','FAILED','CANCELLED')", name="ck_ai_crawl_runs_ai_crawl_run_status"),
        sa.CheckConstraint("trigger_type IN ('SCHEDULED','MANUAL','RECOVERY')", name="ck_ai_crawl_runs_ai_crawl_trigger"),
        sa.ForeignKeyConstraint(["source_id"], ["ai_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_ai_crawl_runs"),
    )
    op.create_index("idx_ai_crawl_runs_source", "ai_crawl_runs", ["source_id", sa.text("queued_at DESC")])
    op.create_index("idx_ai_crawl_runs_status", "ai_crawl_runs", ["status", "queued_at"])

    op.create_table(
        "ai_crawl_items",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_url_id", postgresql.UUID(as_uuid=True)), sa.Column("url", sa.Text(), nullable=False),
        sa.Column("url_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), server_default="DISCOVERED", nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False), sa.Column("discovered_from", sa.Text()),
        sa.Column("http_status", sa.Integer()), sa.Column("content_type", sa.String(255)),
        sa.Column("response_bytes", sa.Integer()), sa.Column("document_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("error_code", sa.String(100)), sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("status IN ('DISCOVERED','FETCHING','UNCHANGED','DOWNLOADED','EXTRACTED','SAVED','REJECTED','FAILED')", name="ck_ai_crawl_items_ai_crawl_item_status"),
        sa.CheckConstraint("depth >= 0", name="ck_ai_crawl_items_ai_crawl_item_depth"),
        sa.ForeignKeyConstraint(["run_id"], ["ai_crawl_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_url_id"], ["ai_source_urls.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_version_id"], ["ai_document_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_ai_crawl_items"),
        sa.UniqueConstraint("run_id", "url_hash", name="uq_ai_crawl_item_url"),
    )
    op.create_index("idx_ai_crawl_items_run", "ai_crawl_items", ["run_id", "status"])


def downgrade() -> None:
    op.drop_table("ai_crawl_items")
    op.drop_table("ai_crawl_runs")
    op.drop_table("ai_source_urls")
    op.drop_table("ai_sources")
