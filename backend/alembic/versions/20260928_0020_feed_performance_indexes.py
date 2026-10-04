"""add indexes for cursor-based feed reads

Revision ID: 20260928_0020
Revises: 20260919_0019
"""

from alembic import op
import sqlalchemy as sa


revision = "20260928_0020"
down_revision = "20260919_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The partial index remains compact because deleted and unapproved posts
    # never belong in a public feed.
    op.create_index(
        "idx_posts_feed_active_cursor", "posts", ["created_at", "id"],
        unique=False,
        postgresql_where=sa.text("status = 'APPROVED' AND deleted_at IS NULL"),
    )
    op.create_index(
        "idx_posts_feed_category_cursor", "posts", ["category", "created_at", "id"],
        unique=False,
        postgresql_where=sa.text("status = 'APPROVED' AND deleted_at IS NULL"),
    )
    op.create_index("idx_post_media_post_sort", "post_media", ["post_id", "sort_order"], unique=False)
    op.create_index(
        "idx_comments_post_preview", "comments", ["post_id", "created_at"], unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_comments_post_preview", table_name="comments")
    op.drop_index("idx_post_media_post_sort", table_name="post_media")
    op.drop_index("idx_posts_feed_category_cursor", table_name="posts")
    op.drop_index("idx_posts_feed_active_cursor", table_name="posts")
