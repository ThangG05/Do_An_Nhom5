"""Regression checks for group report decisions in Test06."""

import uuid
from types import SimpleNamespace

from src.db.models.user import SystemRole
from src.models.report import ReportResolveRequest
from src.services import report_service


class _Result:
    def __init__(self, value=None):
        self.value = value

    def mappings(self):
        return self

    def first(self):
        return self.value


def test_hiding_reported_post_notifies_author_with_reason(monkeypatch):
    report_id, post_id, author_id, reporter_id, admin_id = (uuid.uuid4() for _ in range(5))
    report = {"target_type": "POST", "target_id": post_id, "reporter_id": reporter_id}
    monkeypatch.setattr(report_service, "_target", lambda *_: {"owner_id": author_id})

    class Session:
        def __init__(self):
            self.commands = []
            self.committed = False

        def execute(self, statement, params):
            sql = str(statement)
            self.commands.append((sql, params))
            return _Result(report if "SELECT * FROM reports" in sql else None)

        def scalar(self, statement, _params):
            return author_id if "SELECT author_id FROM posts" in str(statement) else None

        def commit(self):
            self.committed = True

    session = Session()
    report_service.resolve(
        session, SimpleNamespace(id=admin_id, system_role=SystemRole.SUPER_ADMIN),
        report_id, ReportResolveRequest(decision="RESOLVE", action="HIDE_CONTENT", note="Nội dung vi phạm quy định nhóm"),
    )
    notices = [params for sql, params in session.commands if "INSERT INTO notifications" in sql]
    assert session.committed
    assert {notice["uid"] for notice in notices} == {author_id, reporter_id}
    author_notice = next(notice for notice in notices if notice["uid"] == author_id)
    assert "Nội dung vi phạm quy định nhóm" in author_notice["content"]
