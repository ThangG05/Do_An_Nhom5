"""Indexes for unread message badges and recent notification pages.

Revision ID: 20261013_0023
Revises: 20261009_0022
"""

from alembic import op


revision = "20261013_0023"
down_revision = "20261009_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Concurrent builds keep reads and writes available on existing Neon data.
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_message_receipts_unread_user "
            "ON message_receipts (user_id, message_id) WHERE seen_at IS NULL"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_user_recent "
            "ON notifications (user_id, created_at DESC)"
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_notifications_user_recent")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_message_receipts_unread_user")
