"""add deleted post status

Revision ID: 20261009_0022
Revises: 20260928_0021
"""

from alembic import op


revision = "20261009_0022"
down_revision = "20260928_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in a normal downgrade.
    # IF NOT EXISTS keeps this migration idempotent across developer databases.
    op.execute("ALTER TYPE post_status ADD VALUE IF NOT EXISTS 'DELETED'")


def downgrade() -> None:
    pass
