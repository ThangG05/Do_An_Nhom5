"""Add document reference and lifecycle relations.

Revision ID: 20260907_0003
Revises: 20260906_0002
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260907_0003"
down_revision: str | None = "20260906_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_document_relations",
        sa.Column("source_document_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_document_id", postgresql.UUID(as_uuid=True)),
        sa.Column("referenced_number", sa.String(100), nullable=False),
        sa.Column("relation_type", sa.String(30), server_default="REFERENCES", nullable=False),
        sa.Column("context_excerpt", sa.Text()),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint(
            "relation_type IN ('REFERENCES','AMENDS','SUPERSEDES','REPEALS')",
            name="ck_ai_document_relations_ai_document_relation_type",
        ),
        sa.ForeignKeyConstraint(["source_document_version_id"], ["ai_document_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_document_id"], ["ai_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_ai_document_relations"),
        sa.UniqueConstraint("source_document_version_id", "referenced_number", "relation_type",
                            name="uq_ai_document_relation"),
    )
    op.create_index("idx_ai_document_relations_source", "ai_document_relations", ["source_document_version_id"])
    op.create_index("idx_ai_document_relations_target", "ai_document_relations", ["target_document_id"])
    op.create_index("idx_ai_document_relations_number", "ai_document_relations", ["referenced_number"])


def downgrade() -> None:
    op.drop_table("ai_document_relations")
