"""Add maintenance and content moderation configuration."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="20260915_0013";down_revision="20260915_0012";branch_labels=None;depends_on=None
def upgrade():
 op.create_table("system_settings",sa.Column("key",sa.String(100),primary_key=True),sa.Column("value",postgresql.JSONB(),nullable=False,server_default="{}"),sa.Column("updated_by",postgresql.UUID(as_uuid=True),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))
 op.execute("INSERT INTO system_settings(key,value) VALUES('maintenance',jsonb_build_object('enabled',false,'message','Hệ thống đang bảo trì.','expected_end_at',NULL))")
 op.create_table("blacklist_keywords",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,server_default=sa.text("gen_random_uuid()")),sa.Column("keyword",sa.String(255),nullable=False),sa.Column("action",sa.String(20),nullable=False),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("created_by",postgresql.UUID(as_uuid=True),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.UniqueConstraint("keyword",name="uq_blacklist_keyword"),sa.CheckConstraint("action IN ('BLOCK','REVIEW')",name="ck_blacklist_action"))
 op.create_index("idx_blacklist_active","blacklist_keywords",["is_active","keyword"])
def downgrade():op.drop_index("idx_blacklist_active",table_name="blacklist_keywords");op.drop_table("blacklist_keywords");op.drop_table("system_settings")
