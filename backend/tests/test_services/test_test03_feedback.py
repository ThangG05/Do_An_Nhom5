"""Regression checks for Test03 feedback without requiring a live database."""

import uuid
from types import SimpleNamespace

from src.db.models.user import SystemRole
from src.services import report_service


class _Rows:
    def mappings(self):
        return self

    def __iter__(self):
        return iter(())


class _Session:
    def __init__(self, group_ids=()):
        self.group_ids = list(group_ids)
        self.sql = ""
        self.params = {}

    def scalars(self, _statement, _params):
        return self.group_ids

    def execute(self, statement, params):
        self.sql = str(statement)
        self.params = params
        return _Rows()


def test_super_admin_queue_omits_reports_owned_by_active_group_admin():
    session = _Session()
    result = report_service.list_queue(session, SimpleNamespace(system_role=SystemRole.SUPER_ADMIN), "PENDING")
    assert result == []
    assert "NOT EXISTS" in session.sql
    assert "gm.role='ADMIN'" in session.sql
    assert "gu.status='ACTIVE'" in session.sql
    assert session.params["status"] == "PENDING"


def test_group_admin_queue_is_scoped_to_assigned_groups():
    group_id = uuid.uuid4()
    session = _Session([group_id])
    result = report_service.list_queue(session, SimpleNamespace(id=uuid.uuid4(), system_role=SystemRole.USER))
    assert result == []
    assert "COALESCE(p.group_id,cp.group_id)=ANY(:groups)" in session.sql
    assert session.params["groups"] == [group_id]
