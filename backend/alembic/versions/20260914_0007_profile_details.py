"""Persist editable profile details.

Revision ID: 20260914_0007
Revises: 20260914_0006
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260914_0007"
down_revision = "20260914_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("pronouns", sa.String(50), nullable=True))
    op.add_column("profiles", sa.Column("workplace", sa.String(150), nullable=True))
    op.add_column("profiles", sa.Column("education", sa.String(150), nullable=True))
    op.add_column("profiles", sa.Column("current_city", sa.String(150), nullable=True))
    op.add_column("profiles", sa.Column("hometown", sa.String(150), nullable=True))
    op.add_column("profiles", sa.Column("social_links", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False))


def downgrade() -> None:
    for column in ("social_links", "hometown", "current_city", "education", "workplace", "pronouns"):
        op.drop_column("profiles", column)
