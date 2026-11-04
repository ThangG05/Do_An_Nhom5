"""Persist SimHash fingerprints and searchable bands for study files."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20261104_0035"
down_revision = "20261101_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    op.add_column("study_document_files", sa.Column("simhash64", sa.String(16), nullable=True))
    op.create_check_constraint(
        "ck_study_file_simhash64",
        "study_document_files",
        "simhash64 IS NULL OR simhash64 ~ '^[0-9a-f]{16}$'",
    )
    op.create_table(
        "study_document_file_simhash_bands",
        sa.Column("file_id", uuid, sa.ForeignKey("study_document_files.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("group_id", uuid, sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("band_index", sa.SmallInteger(), primary_key=True),
        sa.Column("band_value", sa.Integer(), nullable=False),
        sa.CheckConstraint("band_index >= 0 AND band_index < 11", name="ck_study_simhash_band_index"),
        sa.CheckConstraint("band_value >= 0 AND band_value < 64", name="ck_study_simhash_band_value"),
    )
    op.create_index(
        "idx_study_simhash_band_lookup",
        "study_document_file_simhash_bands",
        ["group_id", "band_index", "band_value"],
    )


def downgrade() -> None:
    op.drop_index("idx_study_simhash_band_lookup", table_name="study_document_file_simhash_bands")
    op.drop_table("study_document_file_simhash_bands")
    op.drop_constraint("ck_study_file_simhash64", "study_document_files", type_="check")
    op.drop_column("study_document_files", "simhash64")
