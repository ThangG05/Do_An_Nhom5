"""Add group membership requests and pinned posts.

Revision ID: 20260915_0010
Revises: 20260915_0009
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260915_0010"
down_revision = "20260915_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    request_status = postgresql.ENUM(
        "PENDING", "APPROVED", "REJECTED",
        name="group_join_request_status",
        create_type=False,
    )
    request_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "group_join_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", request_status, nullable=False, server_default=sa.text("'PENDING'::group_join_request_status")),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_join_request_user"),
    )
    op.create_index("idx_group_join_requests_queue", "group_join_requests", ["group_id", "status", "created_at"])
    op.add_column("posts", sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("idx_posts_group_moderation", "posts", ["group_id", "status", "is_pinned", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_posts_group_moderation", table_name="posts")
    op.drop_column("posts", "is_pinned")
    op.drop_index("idx_group_join_requests_queue", table_name="group_join_requests")
    op.drop_table("group_join_requests")
    postgresql.ENUM(name="group_join_request_status").drop(op.get_bind(), checkfirst=True)
