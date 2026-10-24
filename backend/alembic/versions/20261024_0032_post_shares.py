"""Record in-app post shares for accurate counters."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


revision = "20261024_0032"
down_revision = "20261020_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "post_shares",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("post_id", UUID(as_uuid=True), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("destination_type", sa.String(12), nullable=False),
        sa.Column("destination_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("destination_type", "destination_id", name="uq_post_share_destination"),
    )
    op.create_index("idx_post_shares_post_id", "post_shares", ["post_id"])
    # The first web share UI stored only a URL. Preserve its already-created
    # in-app reposts/messages when introducing the structured counter.
    post_path = r"/posts/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})[[:space:]]*$"
    op.execute(f"""
        INSERT INTO post_shares (id, post_id, actor_id, destination_type, destination_id)
        SELECT gen_random_uuid(), original.id, shared.author_id, 'POST', shared.id
        FROM posts AS shared
        JOIN posts AS original ON original.id = substring(shared.content from '{post_path}')::uuid
        WHERE shared.group_id IS NULL AND shared.deleted_at IS NULL
          AND shared.status = 'APPROVED' AND shared.category = 'general'
        ON CONFLICT (destination_type, destination_id) DO NOTHING
    """)
    op.execute(f"""
        INSERT INTO post_shares (id, post_id, actor_id, destination_type, destination_id)
        SELECT gen_random_uuid(), original.id, message.sender_id, 'MESSAGE', message.id
        FROM messages AS message
        JOIN posts AS original ON original.id = substring(message.content from '{post_path}')::uuid
        WHERE message.deleted_at IS NULL AND message.sender_id IS NOT NULL
        ON CONFLICT (destination_type, destination_id) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_index("idx_post_shares_post_id", table_name="post_shares")
    op.drop_table("post_shares")
