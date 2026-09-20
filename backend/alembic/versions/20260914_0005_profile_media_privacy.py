"""Thêm media R2, bài avatar/cover và quyền riêng tư.

Revision ID: 20260914_0005
Revises: 20260908_0004
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260914_0005"
down_revision = "20260908_0004"
branch_labels = None
depends_on = None

post_visibility = postgresql.ENUM(
    "PUBLIC", "FRIENDS", "PRIVATE", name="post_visibility", create_type=False
)
post_type = postgresql.ENUM(
    "STANDARD", "PROFILE_AVATAR", "PROFILE_COVER", name="post_type", create_type=False
)
media_status = postgresql.ENUM(
    "PENDING", "READY", "FAILED", "DELETED", name="media_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    post_visibility.create(bind, checkfirst=True)
    post_type.create(bind, checkfirst=True)
    media_status.create(bind, checkfirst=True)

    op.add_column("media_files", sa.Column("width", sa.Integer(), nullable=True))
    op.add_column("media_files", sa.Column("height", sa.Integer(), nullable=True))
    op.add_column(
        "media_files",
        sa.Column("status", media_status, server_default="PENDING", nullable=False),
    )
    op.add_column(
        "media_files", sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "media_files", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_check_constraint(
        "ck_media_dimensions",
        "media_files",
        "(width IS NULL OR width > 0) AND (height IS NULL OR height > 0)",
    )
    op.create_check_constraint(
        "ck_media_ready_uploaded",
        "media_files",
        "status <> 'READY' OR uploaded_at IS NOT NULL",
    )
    op.create_index(
        "idx_media_owner_status",
        "media_files",
        ["owner_id", "status", "created_at"],
    )

    op.add_column("profiles", sa.Column("avatar_media_id", postgresql.UUID(), nullable=True))
    op.add_column("profiles", sa.Column("cover_media_id", postgresql.UUID(), nullable=True))
    op.create_foreign_key(
        "profiles_avatar_media_id_fkey",
        "profiles",
        "media_files",
        ["avatar_media_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "profiles_cover_media_id_fkey",
        "profiles",
        "media_files",
        ["cover_media_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_column("profiles", "avatar_object_key")

    op.alter_column("posts", "group_id", existing_type=postgresql.UUID(), nullable=True)
    op.alter_column("posts", "content", existing_type=sa.Text(), server_default="")
    op.add_column(
        "posts",
        sa.Column("post_type", post_type, server_default="STANDARD", nullable=False),
    )
    op.add_column(
        "posts",
        sa.Column("visibility", post_visibility, server_default="PUBLIC", nullable=False),
    )
    op.create_check_constraint(
        "ck_posts_group_scope",
        "posts",
        "((post_type = 'STANDARD' AND group_id IS NOT NULL) OR "
        "(post_type <> 'STANDARD' AND group_id IS NULL))",
    )
    op.create_index(
        "idx_posts_author_visibility",
        "posts",
        ["author_id", "visibility", "status", "created_at"],
    )

    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.create_index("uq_users_email", "users", [sa.text("lower(email)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_users_email", table_name="users")
    op.create_unique_constraint("uq_users_email", "users", ["email"])

    op.drop_index("idx_posts_author_visibility", table_name="posts")
    op.drop_constraint("ck_posts_group_scope", "posts", type_="check")
    op.drop_column("posts", "visibility")
    op.drop_column("posts", "post_type")
    op.alter_column("posts", "content", existing_type=sa.Text(), server_default=None)
    op.alter_column("posts", "group_id", existing_type=postgresql.UUID(), nullable=False)

    op.add_column("profiles", sa.Column("avatar_object_key", sa.Text(), nullable=True))
    op.drop_constraint("profiles_cover_media_id_fkey", "profiles", type_="foreignkey")
    op.drop_constraint("profiles_avatar_media_id_fkey", "profiles", type_="foreignkey")
    op.drop_column("profiles", "cover_media_id")
    op.drop_column("profiles", "avatar_media_id")

    op.drop_index("idx_media_owner_status", table_name="media_files")
    op.drop_constraint("ck_media_ready_uploaded", "media_files", type_="check")
    op.drop_constraint("ck_media_dimensions", "media_files", type_="check")
    op.drop_column("media_files", "deleted_at")
    op.drop_column("media_files", "uploaded_at")
    op.drop_column("media_files", "status")
    op.drop_column("media_files", "height")
    op.drop_column("media_files", "width")

    media_status.drop(op.get_bind(), checkfirst=True)
    post_type.drop(op.get_bind(), checkfirst=True)
    post_visibility.drop(op.get_bind(), checkfirst=True)
