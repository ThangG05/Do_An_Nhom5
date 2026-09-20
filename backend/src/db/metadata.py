"""Alembic metadata for the complete Software + embedded RAG schema."""

from __future__ import annotations

import sys
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import MetaData
from sqlalchemy.dialects import postgresql

from src.db.base import Base as SoftwareBase

# Import every Software ORM module before reading SoftwareBase.metadata.
from src.db.models import chat, friendship, media, notification, post, user  # noqa: F401,E402


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAG_ROOT = PROJECT_ROOT / "RAG"
if str(RAG_ROOT) not in sys.path:
    sys.path.insert(0, str(RAG_ROOT))

# RAG owns its own DeclarativeBase. Importing app.models registers all of its
# tables, including crawler, knowledge, conversation, group and audit tables.
from app.db.base import Base as RAGBase  # noqa: E402
import app.models  # noqa: F401,E402


def build_target_metadata() -> MetaData:
    """Merge both model registries without duplicating shared application tables."""
    metadata = MetaData()
    for table in SoftwareBase.metadata.sorted_tables:
        table.to_metadata(metadata)
    for table in RAGBase.metadata.sorted_tables:
        if table.key not in metadata.tables:
            table.to_metadata(metadata)

    # SQL-first operational tables still belong to Alembic's schema registry.
    join_status = postgresql.ENUM(
        "PENDING", "APPROVED", "REJECTED",
        name="group_join_request_status", create_type=False,
    )
    sa.Table(
        "group_join_requests", metadata,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("group_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", join_status, nullable=False,
                  server_default=sa.text("'PENDING'::group_join_request_status")),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_join_request_user"),
        sa.Index("idx_group_join_requests_queue", "group_id", "status", "created_at"),
    )
    sa.Table(
        "system_settings", metadata,
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    sa.Table(
        "blacklist_keywords", metadata,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("keyword", sa.String(255), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint("keyword", name="uq_blacklist_keyword"),
        sa.CheckConstraint("action IN ('BLOCK','REVIEW')", name="ck_blacklist_action"),
        sa.Index("idx_blacklist_active", "is_active", "keyword"),
    )
    sa.Table(
        "request_rate_limits", metadata,
        sa.Column("identifier", sa.String(255), primary_key=True),
        sa.Column("bucket", sa.String(100), primary_key=True),
        sa.Column("window_start", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Index("idx_rate_limits_cleanup", "window_start"),
    )
    return metadata


target_metadata = build_target_metadata()
