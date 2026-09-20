"""Add category to posts for feed filtering."""
from alembic import op
import sqlalchemy as sa

revision="20260916_0015"
down_revision="20260915_0014"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("posts",sa.Column("category",sa.String(30),nullable=False,server_default="general"))
    op.create_check_constraint("ck_posts_category","posts","category IN ('general','market','roommate','event','study')")
    op.create_index("idx_posts_feed_category","posts",["category","status","created_at"])

def downgrade():
    op.drop_index("idx_posts_feed_category",table_name="posts")
    op.drop_constraint("ck_posts_category","posts",type_="check")
    op.drop_column("posts","category")
