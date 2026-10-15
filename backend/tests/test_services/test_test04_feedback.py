"""Report-target access and previews from Test04 feedback."""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.db.models.post import Comment, Post
from src.db.models.user import SystemRole, User
from src.models.post import CommentAuthorResponse, CommentResponse, PostAuthorResponse, ProfilePostResponse
from src.services import friendship_service, report_service


class _Result:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return self

    def first(self):
        return self.row


class _Session:
    def __init__(self, report, *, active_admin=False, post=None, comment=None, user=None):
        self.report = report
        self.active_admin = active_admin
        self.post = post
        self.comment = comment
        self.user = user

    def execute(self, statement, _params):
        sql = str(statement)
        return _Result(self.report if "FROM reports r" in sql else (1,) if self.active_admin else None)

    def get(self, model, _id):
        return {Post: self.post, Comment: self.comment, User: self.user}.get(model)


def _report(kind="POST", group_id=None):
    return {"target_type": kind, "target_id": uuid.uuid4(), "group_id": group_id}


def _actor(role=SystemRole.USER):
    return SimpleNamespace(id=uuid.uuid4(), system_role=role)


def test_group_admin_cannot_open_report_from_other_group(monkeypatch):
    group_id = uuid.uuid4()
    monkeypatch.setattr(report_service, "_group_ids", lambda _db, _user: [])
    with pytest.raises(HTTPException) as error:
        report_service.get_detail(_Session(_report(group_id=group_id)), _actor(), uuid.uuid4())
    assert error.value.status_code == 403


def test_super_admin_cannot_open_report_owned_by_active_group_admin():
    group_id = uuid.uuid4()
    with pytest.raises(HTTPException) as error:
        report_service.get_detail(_Session(_report(group_id=group_id), active_admin=True), _actor(SystemRole.SUPER_ADMIN), uuid.uuid4())
    assert error.value.status_code == 403


def test_group_admin_can_preview_reported_comment_and_its_post(monkeypatch):
    group_id = uuid.uuid4()
    report = _report("COMMENT", group_id)
    post_id = uuid.uuid4()
    comment = SimpleNamespace(post_id=post_id, deleted_at=None)
    post = SimpleNamespace(deleted_at=None)
    monkeypatch.setattr(report_service, "_group_ids", lambda _db, _user: [group_id])
    post_response = ProfilePostResponse(
        id=str(post_id), author=PostAuthorResponse(id=str(uuid.uuid4()), name="Tác giả", avatar="/assets/logo.png"),
        createdAt=datetime.now(UTC).isoformat(), content="Nội dung bài viết", privacy="public",
    )
    comment_response = CommentResponse(
        id=str(report["target_id"]), author=CommentAuthorResponse(id=str(uuid.uuid4()), name="Người bình luận", avatar="/assets/logo.png"),
        content="Bình luận bị báo cáo", createdAt=datetime.now(UTC).isoformat(),
    )
    monkeypatch.setattr(report_service.post_service, "_serialize_feed_posts", lambda *_args: [post_response])
    monkeypatch.setattr(report_service.post_service, "_comment_response", lambda *_args: comment_response)
    detail = report_service.get_detail(_Session(report, post=post, comment=comment), _actor(), uuid.uuid4())
    assert detail.post.content == "Nội dung bài viết"
    assert detail.comment.content == "Bình luận bị báo cáo"


def test_super_admin_can_preview_reported_user():
    profile = SimpleNamespace(full_name="Nguyễn Văn A", avatar_media_id=None, student_code="26A4041668")
    target = SimpleNamespace(id=uuid.uuid4(), deleted_at=None, profile=profile, username="26a4041668", created_at=datetime.now(UTC), status=SimpleNamespace(value="ACTIVE"))
    detail = report_service.get_detail(_Session(_report("USER"), user=target), _actor(SystemRole.SUPER_ADMIN), uuid.uuid4())
    assert detail.user.name == "Nguyễn Văn A"
    assert detail.user.student_code == "26A4041668"


def test_visited_friend_list_uses_viewer_relationships():
    viewer, owner = _actor(), _actor()
    other = [uuid.uuid4() for _ in range(3)]
    now = datetime.now(UTC)
    friend_rows = [{"friend_id": user_id, "created_at": now} for user_id in [viewer.id, *other]]
    users = [SimpleNamespace(id=user_id, username=f"user_{index}") for index, user_id in enumerate([viewer.id, *other])]
    profiles = [SimpleNamespace(full_name=f"Người {index}", avatar_media_id=None, faculty=None, current_city=None, hometown=None) for index in range(4)]
    responses = [friend_rows, list(zip(users, profiles)), [], [(min(viewer.id, other[0]), max(viewer.id, other[0]))], [(viewer.id, other[1])]]

    class FriendSession:
        def execute(self, *_args, **_kwargs):
            return _ResultWithAll(responses.pop(0))

    result = friendship_service.list_friends(FriendSession(), owner, viewer)
    statuses = {item.id: item.friendshipStatus for item in result}
    assert statuses[str(viewer.id)] == "self"
    assert statuses[str(other[0])] == "friends"
    assert statuses[str(other[1])] == "pending_sent"
    assert statuses[str(other[2])] == "none"
    assert responses == []


class _ResultWithAll:
    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return self

    def all(self):
        return self.rows
