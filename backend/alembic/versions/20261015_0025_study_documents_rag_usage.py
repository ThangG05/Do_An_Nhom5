"""Study-group document library and provider-reported RAG token ledger.

Revision ID: 20261015_0025
Revises: 20261014_0024
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261015_0025"
down_revision = "20261014_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    op.create_table(
        "subjects",
        sa.Column("id", uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("institution", sa.String(150), nullable=False, server_default="Học viện Ngân hàng"),
        sa.Column("source_note", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("length(trim(code)) > 0 AND length(trim(name)) > 0", name="ck_subject_identity"),
    )
    op.create_index("idx_subjects_lookup", "subjects", ["is_active", "name"])

    op.create_table(
        "study_documents",
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
    )
    op.create_index("idx_study_documents_group_status", "study_documents", ["group_id", "status", "created_at"])
    op.create_index("idx_study_documents_owner", "study_documents", ["uploaded_by", "created_at"])
    op.create_index("idx_study_documents_subject", "study_documents", ["subject_id", "created_at"])

    op.create_table(
        "study_document_files",
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
    )
    op.create_index("idx_study_files_document", "study_document_files", ["document_id"])

    op.create_table(
        "rag_token_usage",
        sa.Column("id", uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", uuid, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("request_id", uuid, nullable=False),
        sa.Column("call_index", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(255), nullable=False),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("total_tokens", sa.Integer()),
        sa.Column("usage_source", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("request_id", "call_index", name="uq_rag_token_usage_call"),
        sa.CheckConstraint("call_index > 0", name="ck_rag_usage_call_index"),
        sa.CheckConstraint("input_tokens IS NULL OR input_tokens >= 0", name="ck_rag_usage_input"),
        sa.CheckConstraint("output_tokens IS NULL OR output_tokens >= 0", name="ck_rag_usage_output"),
        sa.CheckConstraint("total_tokens IS NULL OR total_tokens >= 0", name="ck_rag_usage_total"),
    )
    op.create_index("idx_rag_usage_user_time", "rag_token_usage", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("rag_token_usage")
    op.drop_table("study_document_files")
    op.drop_table("study_documents")
    op.drop_table("subjects")
