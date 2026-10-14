from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from scripts.provision_admins import assign_dedicated_group
from src.db.models.user import SystemRole
from src.services import admin_service


class RecordingSession:
    def __init__(self):
        self.statements = []

    def execute(self, statement, params):
        self.statements.append((str(statement), params))


def test_dedicated_admin_keeps_only_own_group():
    session = RecordingSession()
    user = SimpleNamespace(id=uuid4(), email="admin-hoc-tap@hvnh.edu.vn", system_role=SystemRole.USER)
    group = {"id": uuid4(), "slug": "hoc-tap"}

    assign_dedicated_group(session, user, group)

    assert len(session.statements) == 2
    assert "group_id<>:group_id" in session.statements[0][0]
    assert "role='ADMIN'" in session.statements[0][0]
    assert session.statements[0][1] == {"user_id": user.id, "group_id": group["id"]}
    assert "ON CONFLICT" in session.statements[1][0]


def test_dedicated_admin_rejects_mismatched_account():
    session = RecordingSession()
    user = SimpleNamespace(id=uuid4(), email="admin-pass-do@hvnh.edu.vn", system_role=SystemRole.USER)
    with pytest.raises(ValueError):
        assign_dedicated_group(session, user, {"id": uuid4(), "slug": "hoc-tap"})
    assert session.statements == []


def test_super_admin_cannot_grant_dedicated_account_a_different_group(monkeypatch):
    target = SimpleNamespace(id=uuid4(), email="admin-hoc-tap@hvnh.edu.vn")
    monkeypatch.setattr(admin_service, "_target", lambda *_args: target)

    class GroupSession:
        def execute(self, statement, params):
            assert "SELECT name,slug FROM groups" in str(statement)
            return SimpleNamespace(mappings=lambda: SimpleNamespace(first=lambda: {"name": "Pass đồ", "slug": "pass-do"}))

    with pytest.raises(HTTPException) as exc:
        admin_service.set_group_admin(GroupSession(), target.id, uuid4(), SimpleNamespace(id=uuid4()), True)
    assert exc.value.status_code == 409
