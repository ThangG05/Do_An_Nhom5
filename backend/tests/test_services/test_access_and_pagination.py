"""Regression checks without live DB, R2, email or LLM side effects."""
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from src.api.dependencies import require_group_admin
from src.api.endpoints.admin import router
from src.db.models.post import PostStatus, PostVisibility
from src.db.models.user import SystemRole
from src.services import group_service, post_service, study_document_service


@pytest.mark.parametrize("action", ["detail", "comments", "like", "comment"])
def test_blocked_post_is_denied_before_read_or_write(monkeypatch, action):
    db = Mock()
    user = SimpleNamespace(id=uuid4(), system_role=SystemRole.USER)
    post = SimpleNamespace(id=uuid4(), author_id=uuid4(), group_id=None, category="general",
                           visibility=PostVisibility.PUBLIC, status=PostStatus.APPROVED, deleted_at=None)
    db.get.return_value = post
    monkeypatch.setattr(post_service, "is_blocked", lambda *_: True)
    with pytest.raises(HTTPException) as exc:
        if action == "detail": post_service.get_visible_post(db, post.id, user)
        elif action == "comments": post_service.list_comments(db, post.id, user)
        elif action == "like": post_service.set_like(db, post.id, user, True)
        else: post_service.add_comment(db, post.id, user, SimpleNamespace(content="test"))
    assert exc.value.status_code == 403
    db.add.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.parametrize("guard", [require_group_admin, group_service._require_reader,
                                 study_document_service.require_member, study_document_service.require_admin])
def test_super_admin_cannot_bypass_group_role(monkeypatch, guard):
    user = SimpleNamespace(id=uuid4(), system_role=SystemRole.SUPER_ADMIN)
    db = Mock()
    monkeypatch.setattr(study_document_service, "require_study_group", lambda *_: None)
    with pytest.raises(HTTPException) as exc:
        if guard is require_group_admin: guard(uuid4(), user, db)
        else: guard(db, uuid4(), user)
    assert exc.value.status_code == 403


def test_group_admin_needs_assignment_to_requested_group():
    db = Mock()
    user = SimpleNamespace(id=uuid4(), system_role=SystemRole.USER)
    db.execute.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        require_group_admin(uuid4(), user, db)
    assert exc.value.status_code == 403
    db.execute.return_value.first.return_value = (1,)
    assert require_group_admin(uuid4(), user, db) is user


def test_role_assignment_route_removed():
    assert not any(route.path.endswith('/group-admin') for route in router.routes)


@pytest.mark.parametrize("kind", ["profile", "group", "mine"])
def test_pagination_is_applied_in_sql_with_stable_order(monkeypatch, kind):
    db = Mock()
    user = SimpleNamespace(id=uuid4(), system_role=SystemRole.USER)
    db.scalars.return_value.all.return_value = []
    monkeypatch.setattr(group_service, "_group", lambda *_: {})
    monkeypatch.setattr(group_service, "_require_reader", lambda *_: None)
    if kind == "profile":
        post_service.list_profile_posts(db, user, user, limit=11, offset=10, category="event")
    elif kind == "group":
        group_service.list_posts(db, uuid4(), user, query="campus", limit=11, offset=10)
    else:
        group_service.list_my_posts(db, uuid4(), user, limit=11, offset=10)
    statement = db.scalars.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    sql = str(compiled)
    assert statement._limit_clause.value == 11
    assert statement._offset_clause.value == 10
    assert "LIMIT" in sql and "OFFSET" in sql
    assert "posts.id DESC" in sql
    if kind == "profile": assert "event" in compiled.params.values()
    if kind == "group":
        assert "user_blocks" in sql
        assert "%campus%" in compiled.params.values()
