"""Add secure password reset codes."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="20260915_0012";down_revision="20260915_0011";branch_labels=None;depends_on=None
def upgrade():
 op.create_table("password_reset_codes",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("user_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("code_hash",sa.Text(),nullable=False),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),sa.Column("attempts",sa.Integer(),nullable=False,server_default="0"),sa.Column("consumed_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))
 op.create_index("idx_password_reset_active","password_reset_codes",["user_id","created_at"])
def downgrade():op.drop_index("idx_password_reset_active",table_name="password_reset_codes");op.drop_table("password_reset_codes")
