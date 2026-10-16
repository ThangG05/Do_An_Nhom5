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
    uuid = postgresql.UUID(as_uuid=True)
    sa.Table(
        "subjects", metadata,
        sa.Column("id", uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(40), nullable=True),
        sa.Column("category", sa.String(16), nullable=False, server_default="SPECIALIZED"),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("institution", sa.String(150), nullable=False, server_default="Học viện Ngân hàng"),
        sa.Column("source_note", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("length(trim(code)) > 0 AND length(trim(name)) > 0", name="ck_subject_identity"),
        sa.Index("idx_subjects_lookup", "is_active", "name"),
        sa.Index("idx_subjects_code", "code"),
        sa.CheckConstraint("category IN ('GENERAL','SPECIALIZED')", name="ck_subject_category"),
    )
    subjects = metadata.tables["subjects"]
    sa.Index("uq_subject_identity", sa.func.coalesce(subjects.c.code, ""), subjects.c.name,
             subjects.c.category, unique=True)
    sa.Table("majors", metadata,
        sa.Column("id", uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(40), nullable=True, unique=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("source_note", sa.String(500), nullable=False),
    )
    sa.Table("major_subjects", metadata,
        sa.Column("major_id", uuid, sa.ForeignKey("majors.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("subject_id", uuid, sa.ForeignKey("subjects.id", ondelete="RESTRICT"), primary_key=True),
        sa.Index("idx_major_subjects_subject", "subject_id"),
    )
    sa.Table(
        "study_documents", metadata,
        sa.Column("id", uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("group_id", uuid, sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_id", uuid, sa.ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("uploaded_by", uuid, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("total_bytes", sa.BigInteger(), nullable=False),
        sa.Column("file_count", sa.Integer(), nullable=False),
        sa.Column("reviewed_by", uuid, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("rejection_reason", sa.String(2000)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('PENDING','APPROVED','REJECTED')", name="ck_study_document_status"),
        sa.CheckConstraint("total_bytes > 0 AND total_bytes <= 52428800", name="ck_study_document_size"),
        sa.CheckConstraint("file_count > 0 AND file_count <= 10", name="ck_study_document_files"),
        sa.Index("idx_study_documents_group_status", "group_id", "status", "created_at"),
        sa.Index("idx_study_documents_owner", "uploaded_by", "created_at"),
        sa.Index("idx_study_documents_subject", "subject_id", "created_at"),
    )
    sa.Table(
        "study_document_files", metadata,
        sa.Column("id", uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", uuid, sa.ForeignKey("study_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("r2_object_key", sa.String(500), nullable=False, unique=True),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(150), nullable=False),
        sa.Column("extension", sa.String(10), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("size_bytes > 0 AND size_bytes <= 52428800", name="ck_study_file_size"),
        sa.Index("idx_study_files_document", "document_id"),
    )
    return metadata


target_metadata = build_target_metadata()
