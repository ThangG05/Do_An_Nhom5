"""Index active study-file checksums for exact duplicate preflight."""

from alembic import op
import sqlalchemy as sa


revision = "20261029_0033"
down_revision = "20261024_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_study_files_checksum_active",
        "study_document_files",
        ["checksum_sha256"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_study_files_checksum_active", table_name="study_document_files")
