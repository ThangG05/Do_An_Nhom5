"""Harden report workflow and prevent duplicate open reports.

Revision ID: 20260915_0011
Revises: 20260915_0010
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="20260915_0011";down_revision="20260915_0010";branch_labels=None;depends_on=None

def upgrade()->None:
    op.add_column("reports",sa.Column("evidence_media_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("media_files.id",ondelete="SET NULL"),nullable=True))
    op.execute("CREATE INDEX IF NOT EXISTS idx_reports_queue ON reports (status,created_at)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_reports_open_target ON reports (reporter_id,target_type,target_id) WHERE status IN ('PENDING','REVIEWING')")

def downgrade()->None:
    op.execute("DROP INDEX IF EXISTS uq_reports_open_target");op.drop_column("reports","evidence_media_id")
