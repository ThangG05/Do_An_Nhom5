"""Add group-scoped reports for shared study documents."""
from alembic import op
import sqlalchemy as sa

revision = "20261017_0027"
down_revision = "20261016_0026"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "study_document_reports",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("group_id", sa.UUID(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.UUID(), sa.ForeignKey("study_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reporter_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reporter_name", sa.String(255), nullable=False),
        sa.Column("reason", sa.String(3000), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="OPEN"),
        sa.Column("resolution_note", sa.String(3000)),
        sa.Column("handled_by", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("handled_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('OPEN','RESOLVED','DISMISSED')", name="ck_study_document_report_status"),
    )
    op.create_index("idx_study_doc_reports_group_status", "study_document_reports", ["group_id", "status", "created_at"])
    op.create_index("idx_study_doc_reports_document", "study_document_reports", ["document_id", "created_at"])
    op.create_index("uq_study_doc_report_open_user", "study_document_reports", ["document_id", "reporter_id"],
                    unique=True, postgresql_where=sa.text("status = 'OPEN'"))


def downgrade():
    op.drop_table("study_document_reports")
