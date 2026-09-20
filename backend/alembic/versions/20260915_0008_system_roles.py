"""Add global system roles.

Revision ID: 20260915_0008
Revises: 20260914_0007
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260915_0008"
down_revision = "20260914_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    system_role = postgresql.ENUM("USER", "SUPER_ADMIN", name="system_role")
    system_role.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column(
            "system_role",
            system_role,
            server_default=sa.text("'USER'::system_role"),
            nullable=False,
        ),
    )
    op.create_index("idx_users_system_role", "users", ["system_role"])


def downgrade() -> None:
    op.drop_index("idx_users_system_role", table_name="users")
    op.drop_column("users", "system_role")
    postgresql.ENUM(name="system_role").drop(op.get_bind(), checkfirst=True)
