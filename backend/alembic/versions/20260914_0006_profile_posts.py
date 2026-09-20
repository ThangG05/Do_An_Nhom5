"""Add a dedicated profile post type.

Revision ID: 20260914_0006
Revises: 20260914_0005
"""
from alembic import op

revision = "20260914_0006"
down_revision = "20260914_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE post_type ADD VALUE IF NOT EXISTS 'PROFILE_POST'")


def downgrade() -> None:
    pass
