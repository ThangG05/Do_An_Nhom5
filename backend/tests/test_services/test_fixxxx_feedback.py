"""Guard the scope and transitions of proactive public-feed moderation."""

import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from src.db.models.post import PostStatus, PostVisibility
from src.api.endpoints import users as users_endpoint
from src.services.admin_service import moderate_public_post


@pytest.mark.parametrize("group_id,visibility,deleted", [
    (uuid.uuid4(), PostVisibility.PUBLIC, None),
    (None, PostVisibility.FRIENDS, None),
    (None, PostVisibility.PUBLIC, object()),
])
def test_admin_cannot_moderate_non_public_or_group_posts(group_id, visibility, deleted):
    post = SimpleNamespace(group_id=group_id, visibility=visibility, deleted_at=deleted)
    db = Mock()
    db.scalar.return_value = post
    with pytest.raises(HTTPException) as error:
        moderate_public_post(db, uuid.uuid4(), SimpleNamespace(id=uuid.uuid4()), "HIDE", "Vi phạm")
    assert error.value.status_code == 404
    db.commit.assert_not_called()


def test_admin_hide_and_restore_public_post_writes_audit():
    admin = SimpleNamespace(id=uuid.uuid4())
    post = SimpleNamespace(id=uuid.uuid4(), group_id=None, visibility=PostVisibility.PUBLIC,
                           deleted_at=None, status=PostStatus.APPROVED,
                           reviewed_by=None, reviewed_at=None, rejection_reason=None)
    db = Mock()
    db.scalar.return_value = post

    moderate_public_post(db, post.id, admin, "HIDE", "Nội dung vi phạm")
    assert post.status == PostStatus.HIDDEN
    assert post.rejection_reason == "Nội dung vi phạm"
    assert post.reviewed_by == admin.id
    assert db.execute.call_args.args[1]["action"] == "PUBLIC_POST_HIDE"

    moderate_public_post(db, post.id, admin, "RESTORE", "Đã xác minh")
    assert post.status == PostStatus.APPROVED
    assert post.rejection_reason is None
    assert db.execute.call_args.args[1]["action"] == "PUBLIC_POST_RESTORE"
    assert db.commit.call_count == 2


def test_admin_cannot_repeat_same_transition():
    post = SimpleNamespace(id=uuid.uuid4(), group_id=None, visibility=PostVisibility.PUBLIC,
                           deleted_at=None, status=PostStatus.HIDDEN)
    db = Mock()
    db.scalar.return_value = post
    with pytest.raises(HTTPException) as error:
        moderate_public_post(db, post.id, SimpleNamespace(id=uuid.uuid4()), "HIDE", "Lý do")
    assert error.value.status_code == 409
    db.commit.assert_not_called()


def test_blocked_list_uses_profile_avatar_not_institution_logo(monkeypatch):
    user_id, avatar_id = uuid.uuid4(), uuid.uuid4()
    user = SimpleNamespace(id=user_id, username="student", deleted_at=None)
    profile = SimpleNamespace(full_name="Sinh viên", avatar_media_id=avatar_id, faculty="CNTT")
    media = SimpleNamespace(id=avatar_id)
    db = Mock()
    db.scalars.side_effect = [[user_id], [media]]
    db.execute.return_value.all.return_value = [(user, profile)]
    monkeypatch.setattr(users_endpoint, "create_download_url", lambda _: "https://cdn.example/avatar.jpg")

    result = users_endpoint.blocked_users(SimpleNamespace(id=uuid.uuid4()), db)

    assert len(result) == 1
    assert result[0].avatar == "https://cdn.example/avatar.jpg"
    assert result[0].name == "Sinh viên"
