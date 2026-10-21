"""Persist AI advice separately from human document decisions."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "20261020_0031"
down_revision = "20261020_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "study_document_ai_assessments",
        sa.Column("document_id", sa.UUID(), sa.ForeignKey("study_documents.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="QUEUED"),
        sa.Column("recommendation", sa.String(20)),
        sa.Column("file_results", JSONB),
        sa.Column("reason", sa.Text()),
        sa.Column("model_name", sa.String(100)),
        sa.Column("prompt_version", sa.String(40)),
        sa.Column("error_code", sa.String(80)),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("claimed_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('QUEUED','PROCESSING','COMPLETED','FAILED')", name="ck_study_ai_status"),
        sa.CheckConstraint("recommendation IS NULL OR recommendation IN ('APPROVE','REJECT','REVIEW')", name="ck_study_ai_recommendation"),
    )
    op.create_index("idx_study_ai_queue", "study_document_ai_assessments", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_study_ai_queue", table_name="study_document_ai_assessments")
    op.drop_table("study_document_ai_assessments")
