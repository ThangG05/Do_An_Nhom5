import uuid

import pytest
from sqlalchemy import text

from src.db.models.user import SystemRole
from src.services import study_document_service as library


def test_study_library_requires_membership_and_admin_review(
    client, db_session, make_user, auth_headers, monkeypatch,
):
    group_id = db_session.execute(text(
        "SELECT id FROM groups WHERE slug='hoc-tap' AND status='ACTIVE'"
    )).scalar_one_or_none()
    if group_id is None:
        pytest.skip("Chưa có nhóm Học tập để chạy kiểm thử tích hợp.")

    owner = make_user(name="Người chia sẻ")
    reviewer = make_user(name="Admin Học tập")
    member = make_user(name="Thành viên")
    outsider = make_user(name="Người ngoài nhóm")
    superadmin = make_user(role=SystemRole.SUPER_ADMIN)
    for user, role in ((owner, "MEMBER"), (reviewer, "ADMIN"), (member, "MEMBER")):
        db_session.execute(text("""
            INSERT INTO group_members(group_id,user_id,role)
            VALUES(:gid,:uid,:role)
            ON CONFLICT(group_id,user_id) DO UPDATE SET role=EXCLUDED.role
        """), {"gid": group_id, "uid": user.id, "role": role})
    db_session.commit()

    class FakeR2:
        def __init__(self):
            self.uploads = []
            self.deletes = []
        def upload_fileobj(self, stream, bucket, key, ExtraArgs):
            self.uploads.append((bucket, key, stream.read(), ExtraArgs))
        def generate_presigned_url(self, operation, Params, ExpiresIn):
            assert Params["Bucket"] == "test-private-study"
            assert ExpiresIn <= 300
            return "https://r2.test/signed-download"
        def delete_object(self, Bucket, Key):
            self.deletes.append((Bucket, Key))

    r2 = FakeR2()
    monkeypatch.setattr(library, "get_r2_client", lambda: r2)
    monkeypatch.setattr(library.settings, "R2_STUDY_BUCKET_NAME", "test-private-study")
    major_id = db_session.execute(text("SELECT id FROM majors WHERE code='IT01'")).scalar_one()
    subject = client.put("/api/v1/admin/subjects", headers=auth_headers(superadmin), json={
        "code": f"IT{uuid.uuid4().hex[:10]}", "name": "Môn kiểm thử tích hợp",
        "source_note": "Nguồn thử nghiệm tích hợp", "is_active": True,
        "major_ids": [str(major_id)],
    })
    assert subject.status_code == 200, subject.text

    created = client.post(f"/api/v1/groups/{group_id}/library", headers=auth_headers(owner), data={
        "subject_id": subject.json()["id"], "title": "Slide chương một",
    }, files=[("files", ("slide.pdf", b"%PDF-1.7\nexample", "application/pdf"))])
    assert created.status_code == 201, created.text
    doc = created.json()
    assert doc["status"] == "PENDING"
    assert r2.uploads[0][0] == "test-private-study"
    assert r2.uploads[0][1].startswith(f"study-groups/{group_id}/documents/")

    path = f"/api/v1/groups/{group_id}/library"
    assert client.get(path, headers=auth_headers(outsider)).status_code == 403
    assert client.get(path, headers=auth_headers(member)).json() == []
    file_path = f"{path}/{doc['id']}/files/{doc['files'][0]['id']}/download"
    assert client.get(file_path, headers=auth_headers(member)).status_code == 404
    assert len(client.get(f"{path}/admin/pending", headers=auth_headers(reviewer)).json()) == 1

    approved = client.patch(f"{path}/admin/{doc['id']}", headers=auth_headers(reviewer),
                            json={"decision": "APPROVE"})
    assert approved.status_code == 200, approved.text
    assert len(client.get(path, headers=auth_headers(member)).json()) == 1
    assert len(client.get(path, params={"major_id": str(major_id)}, headers=auth_headers(member)).json()) == 1
    assert client.get(path, params={"category": "GENERAL"}, headers=auth_headers(member)).json() == []
    assert client.get(path, params={"major_id": str(uuid.uuid4())}, headers=auth_headers(member)).json() == []
    download = client.get(file_path, headers=auth_headers(member))
    assert download.status_code == 200
    assert download.json()["url"] == "https://r2.test/signed-download"

    report_path = f"{path}/{doc['id']}/reports"
    reported = client.post(report_path, headers=auth_headers(member), json={
        "reason": "Tài liệu có nội dung không phù hợp với môn học.",
    })
    assert reported.status_code == 201, reported.text
    assert client.post(report_path, headers=auth_headers(owner), json={
        "reason": "Tự tố cáo tài liệu của mình.",
    }).status_code == 400
    assert client.post(report_path, headers=auth_headers(member), json={
        "reason": "Nội dung khác.",
    }).status_code == 409
    assert client.get(f"{path}/admin/reports/count", headers=auth_headers(reviewer)).json() == {"count": 1}
    assert client.get(f"{path}/admin/reports", headers=auth_headers(reviewer)).json()[0]["reason"] == \
        "Tài liệu có nội dung không phù hợp với môn học."
    assert client.get(f"{path}/admin/reports", headers=auth_headers(member)).status_code == 403

    dismissed = client.patch(f"{path}/admin/reports/{reported.json()['id']}",
                             headers=auth_headers(reviewer), json={
                                 "decision": "DISMISS", "note": "Tài liệu phù hợp nội dung môn học.",
                             })
    assert dismissed.status_code == 200, dismissed.text
    assert client.get(f"{path}/admin/reports/count", headers=auth_headers(reviewer)).json() == {"count": 0}

    second_report = client.post(report_path, headers=auth_headers(member), json={
        "reason": "Tài liệu chứa nội dung vi phạm quy định kho học tập.",
    })
    assert second_report.status_code == 201, second_report.text
    removed = client.patch(f"{path}/admin/reports/{second_report.json()['id']}",
                           headers=auth_headers(reviewer), json={
                               "decision": "REMOVE_DOCUMENT", "note": "Tài liệu vi phạm quy định chia sẻ.",
                           })
    assert removed.status_code == 200, removed.text
    assert len(r2.deletes) == 1
    assert client.get(path, headers=auth_headers(member)).json() == []
