"""Cache derived study-document fingerprints to avoid repeated OCR calls."""

from alembic import op
import sqlalchemy as sa


revision = "20261104_0036"
down_revision = "20261104_0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "study_document_scan_fingerprint_cache",
        sa.Column("checksum_sha256", sa.String(64), primary_key=True),
        sa.Column("extension", sa.String(10), primary_key=True),
        sa.Column("algorithm_version", sa.SmallInteger(), primary_key=True),
        sa.Column("simhash64", sa.String(16), nullable=True),
        sa.Column("scan_status", sa.String(24), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("checksum_sha256 ~ '^[0-9a-f]{64}$'", name="ck_study_scan_cache_sha256"),
        sa.CheckConstraint("simhash64 IS NULL OR simhash64 ~ '^[0-9a-f]{16}$'",
                           name="ck_study_scan_cache_simhash64"),
        sa.CheckConstraint("scan_status IN ('SCANNED','OCR_SCANNED','NO_TEXT','UNSUPPORTED')",
                           name="ck_study_scan_cache_status"),
    )


def downgrade() -> None:
    op.drop_table("study_document_scan_fingerprint_cache")
