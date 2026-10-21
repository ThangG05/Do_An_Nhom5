"""Add structured study-document metadata without guessing legacy values."""

from alembic import op
import sqlalchemy as sa


revision = "20261020_0030"
down_revision = "20261019_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("study_documents", sa.Column("major_id", sa.UUID(), nullable=True))
    op.add_column("study_documents", sa.Column("document_type", sa.String(20), nullable=True))
    op.add_column("study_documents", sa.Column("assessment_type", sa.String(20), nullable=True))
    op.create_foreign_key("fk_study_documents_major", "study_documents", "majors", ["major_id"], ["id"], ondelete="RESTRICT")
    op.create_check_constraint(
        "ck_study_document_type", "study_documents",
        "document_type IS NULL OR document_type IN ('EXAM','EXERCISE','LECTURE','REVIEW','OTHER')",
    )
    op.create_check_constraint(
        "ck_study_assessment_type", "study_documents",
        "assessment_type IS NULL OR assessment_type IN ('MIDTERM','FINAL')",
    )
    op.create_check_constraint(
        "ck_study_assessment_applicability", "study_documents",
        "assessment_type IS NULL OR document_type IN ('EXAM','EXERCISE','REVIEW')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_study_assessment_applicability", "study_documents")
    op.drop_constraint("ck_study_assessment_type", "study_documents")
    op.drop_constraint("ck_study_document_type", "study_documents")
    op.drop_constraint("fk_study_documents_major", "study_documents")
    op.drop_column("study_documents", "assessment_type")
    op.drop_column("study_documents", "document_type")
    op.drop_column("study_documents", "major_id")
