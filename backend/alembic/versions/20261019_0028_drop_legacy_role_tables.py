"""Remove the unused legacy role mapping tables.

Authorization uses users.system_role and group_members.role instead.
"""

from alembic import op
import sqlalchemy as sa


revision = "20261019_0028"
down_revision = "20261017_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Do not use CASCADE: an unexpected external dependency must stop migration.
    op.drop_table("user_roles")
    op.drop_table("roles")


def downgrade() -> None:
    # Restores the old structure, not data removed by the upgrade.
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text()),
        sa.UniqueConstraint("code", name="roles_code_key"),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.UUID(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="user_roles_pkey"),
    )
