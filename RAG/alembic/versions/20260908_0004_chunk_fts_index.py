"""add PostgreSQL full-text index for hybrid retrieval

Revision ID: 20260908_0004
Revises: 20260907_0003
"""
from alembic import op

revision = "20260908_0004"
down_revision = "20260907_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX idx_ai_chunks_content_fts ON ai_document_chunks "
        "USING gin (to_tsvector('simple'::regconfig, coalesce(content, '')))"
    )


def downgrade() -> None:
    op.drop_index("idx_ai_chunks_content_fts", table_name="ai_document_chunks")
