"""Add distributed rate limits and temporary login lockouts."""
from alembic import op
import sqlalchemy as sa
revision="20260915_0014";down_revision="20260915_0013";branch_labels=None;depends_on=None
def upgrade():
 op.add_column("users",sa.Column("failed_login_attempts",sa.Integer(),nullable=False,server_default="0"));op.add_column("users",sa.Column("login_locked_until",sa.DateTime(timezone=True),nullable=True))
 op.create_table("request_rate_limits",sa.Column("identifier",sa.String(255),nullable=False),sa.Column("bucket",sa.String(100),nullable=False),sa.Column("window_start",sa.DateTime(timezone=True),nullable=False),sa.Column("request_count",sa.Integer(),nullable=False,server_default="1"),sa.PrimaryKeyConstraint("identifier","bucket","window_start",name="request_rate_limits_pkey"));op.create_index("idx_rate_limits_cleanup","request_rate_limits",["window_start"])
def downgrade():op.drop_index("idx_rate_limits_cleanup",table_name="request_rate_limits");op.drop_table("request_rate_limits");op.drop_column("users","login_locked_until");op.drop_column("users","failed_login_attempts")
