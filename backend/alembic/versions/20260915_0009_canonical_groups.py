"""Create the four canonical business groups.

Revision ID: 20260915_0009
Revises: 20260915_0008
"""
from alembic import op

revision = "20260915_0009"
down_revision = "20260915_0008"
branch_labels = None
depends_on = None


GROUPS = (
    ("b1000000-0000-0000-0000-000000000001", "Pass đồ", "pass-do", "Trao đổi giáo trình, tài liệu và đồ dùng sinh viên."),
    ("b1000000-0000-0000-0000-000000000002", "Ghép phòng / Tìm phòng trọ", "ghep-phong-tim-tro", "Tìm người ở ghép và phòng trọ quanh Học viện."),
    ("b1000000-0000-0000-0000-000000000003", "Sự kiện", "su-kien", "Tin tức, cuộc thi và hoạt động ngoại khóa."),
    ("b1000000-0000-0000-0000-000000000004", "Học tập", "hoc-tap", "Tài liệu, đề thi mẫu và thảo luận học tập."),
)


def upgrade() -> None:
    for group_id, name, slug, description in GROUPS:
        op.execute(
            "INSERT INTO groups (id,name,slug,description,status) "
            f"VALUES ('{group_id}'::uuid, '{name.replace(chr(39), chr(39) * 2)}', "
            f"'{slug}', '{description.replace(chr(39), chr(39) * 2)}', 'ACTIVE') "
            "ON CONFLICT (slug) DO NOTHING"
        )


def downgrade() -> None:
    slugs = ",".join(f"'{group[2]}'" for group in GROUPS)
    op.execute(f"DELETE FROM groups WHERE slug IN ({slugs})")
