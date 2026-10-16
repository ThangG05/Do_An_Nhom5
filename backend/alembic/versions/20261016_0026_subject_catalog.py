"""Import the supplied HVNH catalog, preserving conflicting names and missing codes."""
import json
from pathlib import Path
import uuid

from alembic import op
import sqlalchemy as sa

revision = "20261016_0026"
down_revision = "20261015_0025"
branch_labels = None
depends_on = None


def insert_batch(connection, name, rows):
    # One SQL statement per table, avoiding hundreds of remote DB round trips.
    if rows:
        table = sa.table(name, *(sa.column(key) for key in rows[0]))
        connection.execute(table.insert().values(rows))


def upgrade():
    op.drop_constraint("subjects_code_key", "subjects", type_="unique")
    op.alter_column("subjects", "code", existing_type=sa.String(40), nullable=True)
    op.add_column("subjects", sa.Column("category", sa.String(16), nullable=False, server_default="SPECIALIZED"))
    op.add_column("subjects", sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_check_constraint("ck_subject_category", "subjects", "category IN ('GENERAL','SPECIALIZED')")
    op.create_index("idx_subjects_code", "subjects", ["code"])
    op.execute("CREATE UNIQUE INDEX uq_subject_identity ON subjects (COALESCE(code,''), name, category)")
    op.create_table("majors",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(40), nullable=True, unique=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("source_note", sa.String(500), nullable=False),
    )
    op.create_table("major_subjects",
        sa.Column("major_id", sa.UUID(), sa.ForeignKey("majors.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("subject_id", sa.UUID(), sa.ForeignKey("subjects.id", ondelete="RESTRICT"), primary_key=True),
    )
    op.create_index("idx_major_subjects_subject", "major_subjects", ["subject_id"])
    connection = op.get_bind()
    catalog = json.loads((Path(__file__).parent.parent / "data/hvnh_catalog_20261016.json").read_text(encoding="utf-8"))
    assert len(catalog["majors"]) == 18 and len(catalog["subjects"]) == 355 and len(catalog["links"]) == 481
    existing = {(r.code, r.name, r.category): r.id for r in connection.execute(sa.text("SELECT id,code,name,category FROM subjects"))}
    new_subjects = []
    for subject in catalog["subjects"]:
        key = (subject["code"], subject["name"], subject["category"])
        if key not in existing:
            existing[key] = uuid.uuid5(uuid.NAMESPACE_URL, "hvnh-subject:" + json.dumps(key, ensure_ascii=False))
            new_subjects.append({**subject, "id": existing[key], "source_note": catalog["source"]})
    insert_batch(connection, "subjects", new_subjects)
    majors = {m["name"]: uuid.uuid5(uuid.NAMESPACE_URL, "hvnh-major:" + m["name"]) for m in catalog["majors"]}
    insert_batch(connection, "majors",
        [{**m, "id": majors[m["name"]], "source_note": catalog["source"]} for m in catalog["majors"]])
    insert_batch(connection, "major_subjects",
        [{"major_id": majors[l["major"]], "subject_id": existing[(l["code"], l["name"], "SPECIALIZED")]} for l in catalog["links"]])
    connection.execute(sa.text("""UPDATE subjects SET needs_review=true WHERE code IS NULL OR code IN
        (SELECT code FROM subjects WHERE code IS NOT NULL GROUP BY code HAVING count(DISTINCT name)>1)"""))


def downgrade():
    # A rollback to code-only identity would lose conflicting subjects and their documents.
    raise RuntimeError("Catalog downgrade requires a reviewed data migration; no catalog data was removed.")
