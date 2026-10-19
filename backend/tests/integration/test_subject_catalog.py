import uuid
from sqlalchemy import text

from src.db.models.user import SystemRole


def test_catalog_filters_identity_and_permissions(client, db_session, make_user, auth_headers):
    superadmin, admin, member = make_user(role=SystemRole.SUPER_ADMIN), make_user(), make_user()
    admin_auth, member_auth = auth_headers(admin), auth_headers(member)
    group_id = db_session.execute(text("SELECT id FROM groups WHERE slug='hoc-tap' AND status='ACTIVE'")).scalar_one()
    db_session.execute(text("INSERT INTO group_members(group_id,user_id,role) VALUES(:gid,:uid,'ADMIN') ON CONFLICT(group_id,user_id) DO UPDATE SET role='ADMIN'"), {"gid": group_id, "uid": admin.id})
    db_session.commit()
    subject_path = f"/api/v1/groups/{group_id}/library/admin/subjects"
    majors = client.get("/api/v1/majors", headers=member_auth)
    assert majors.status_code == 200
    it = next(m for m in majors.json() if m["code"] == "IT01")
    subjects = client.get(f"/api/v1/subjects?major_id={it['id']}", headers=member_auth).json()
    assert len(subjects) == 30
    collision = [s for s in subjects if s["code"] == "IS53A"]
    assert len(collision) == 2 and all(s["needs_review"] for s in collision)
    assert len({s["id"] for s in collision}) == 2
    assert len(client.get("/api/v1/subjects?category=GENERAL", headers=member_auth).json()) == 29
    pages = [client.get(f"/api/v1/subjects?offset={offset}", headers=member_auth).json() for offset in (0, 50)]
    assert len(pages[0]) == len(pages[1]) == 50
    assert not ({s["id"] for s in pages[0]} & {s["id"] for s in pages[1]})
    payload = {"code": "TEST" + uuid.uuid4().hex[:8], "name": "Môn kiểm thử A", "source_note": "Nguồn kiểm thử"}
    assert client.put(subject_path, headers=member_auth, json=payload).status_code == 403
    assert client.put(subject_path, headers=auth_headers(superadmin), json=payload).status_code == 403
    a = client.put(subject_path, headers=admin_auth, json=payload).json()
    b_response = client.put(subject_path, headers=admin_auth, json={**payload, "name": "Môn kiểm thử B", "major_ids": [it["id"]]})
    assert b_response.status_code == 200, b_response.text
    b = b_response.json()
    assert a["id"] != b["id"]
    changed = client.put(subject_path, headers=admin_auth, json={**b, "is_active": False})
    assert changed.status_code == 200
    assert db_session.execute(text("SELECT is_active FROM subjects WHERE id=:id"), {"id": a["id"]}).scalar() is True
    missing = client.put(subject_path, headers=admin_auth, json={**payload, "code": None, "name": "Chưa có mã " + uuid.uuid4().hex})
    assert missing.status_code == 200 and missing.json()["code"] is None


def test_migration_imports_full_catalog_without_overwriting_existing_subject(db_session):
    import importlib.util
    from pathlib import Path
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    connection = db_session.connection()
    savepoint = connection.begin_nested()
    try:
        schema = "catalog_test_" + uuid.uuid4().hex
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'SET LOCAL search_path TO "{schema}", public'))
        connection.execute(text("""CREATE TABLE subjects (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(), code varchar(40) NOT NULL UNIQUE,
            name varchar(255) NOT NULL, institution varchar(150) NOT NULL DEFAULT 'HVNH',
            source_note varchar(500) NOT NULL, is_active boolean NOT NULL DEFAULT true,
            created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now())"""))
        existing_id = uuid.uuid4()
        connection.execute(text("INSERT INTO subjects(id,code,name,source_note) VALUES(:id,'IS53A','Tên môn cũ cần giữ','Nguồn trước import')"), {"id": existing_id})
        path = Path(__file__).resolve().parents[2] / "alembic/versions/20261016_0026_subject_catalog.py"
        spec = importlib.util.spec_from_file_location("catalog_migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with Operations.context(MigrationContext.configure(connection)):
            module.upgrade()
        assert connection.execute(text("SELECT count(*) FROM subjects")).scalar() == 356
        assert connection.execute(text("SELECT count(*) FROM majors")).scalar() == 18
        assert connection.execute(text("SELECT count(*) FROM major_subjects")).scalar() == 481
        assert connection.execute(text("SELECT name FROM subjects WHERE id=:id"), {"id": existing_id}).scalar() == "Tên môn cũ cần giữ"
    finally:
        savepoint.rollback()
