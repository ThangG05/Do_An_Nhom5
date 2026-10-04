"""store selected location on posts

Revision ID: 20260928_0021
Revises: 20260928_0020
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260928_0021"
down_revision = "20260928_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("location_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("posts", "location_data")
