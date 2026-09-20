"""store structured listing data on posts

Revision ID: 20260917_0018
Revises: 20260916_0017
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260917_0018"
down_revision = "20260916_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("listing_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("posts", "listing_data")
