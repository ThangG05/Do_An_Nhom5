"""Add Super Admin discipline metadata."""
from alembic import op
import sqlalchemy as sa
revision="20260916_0017";down_revision="20260916_0016";branch_labels=None;depends_on=None
def upgrade():
    op.add_column("users",sa.Column("suspended_until",sa.DateTime(timezone=True),nullable=True))
    op.add_column("users",sa.Column("warning_count",sa.Integer(),nullable=False,server_default="0"))
def downgrade():
    op.drop_column("users","warning_count");op.drop_column("users","suspended_until")
