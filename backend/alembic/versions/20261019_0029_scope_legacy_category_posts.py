"""Attach legacy public category posts to their canonical groups.

Older posts were saved as profile posts with group_id NULL. That bypassed
membership filtering in the home feed even though these categories now belong
to private groups.
"""

from alembic import op


revision = "20261019_0029"
down_revision = "20261019_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        UPDATE posts AS post
        SET group_id = group_row.id, post_type = 'STANDARD'
        FROM groups AS group_row
        WHERE post.group_id IS NULL
          AND post.deleted_at IS NULL
          AND post.visibility = 'PUBLIC'
          AND group_row.status = 'ACTIVE'
          AND group_row.slug = CASE post.category
              WHEN 'market' THEN 'pass-do'
              WHEN 'roommate' THEN 'ghep-phong-tim-tro'
              WHEN 'event' THEN 'su-kien'
              WHEN 'study' THEN 'hoc-tap'
          END
    """)


def downgrade() -> None:
    # Group IDs cannot be safely distinguished from subsequently published posts.
    pass
