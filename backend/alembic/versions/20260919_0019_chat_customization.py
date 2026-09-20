"""add conversation customization

Revision ID: 20260919_0019
Revises: 20260917_0018
"""

from alembic import op
import sqlalchemy as sa

revision = "20260919_0019"
down_revision = "20260917_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("conversations", sa.Column("theme", sa.String(length=30), server_default="blue", nullable=False))
    op.add_column("conversation_members", sa.Column("nickname", sa.String(length=100), nullable=True))
    op.add_column("conversation_members", sa.Column("is_muted", sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    op.drop_column("conversation_members", "is_muted")
    op.drop_column("conversation_members", "nickname")
    op.drop_column("conversations", "theme")
