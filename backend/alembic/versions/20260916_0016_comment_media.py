"""Add image attachments to comments."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="20260916_0016";down_revision="20260916_0015";branch_labels=None;depends_on=None
def upgrade():
    op.add_column("comments",sa.Column("media_id",postgresql.UUID(as_uuid=True),nullable=True))
    op.create_foreign_key("fk_comments_media_id","comments","media_files",["media_id"],["id"],ondelete="SET NULL")
def downgrade():
    op.drop_constraint("fk_comments_media_id","comments",type_="foreignkey")
    op.drop_column("comments","media_id")
