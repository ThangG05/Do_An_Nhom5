"""Fast, database-independent checks for the Test05 feedback fixes."""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from unittest.mock import Mock

from src.db.models.chat import Message
from src.db.models.post import Comment
from src.db.models.user import Profile, SystemRole, User
from src.models.report import ReportResolveRequest
from src.services import chat_service, post_service, report_service


class _Row:
    def __init__(self, value=None):
        self.value = value

    def mappings(self):
        return self

    def first(self):
        return self.value

    def __iter__(self):
        return iter(())


def test_deleting_own_comment_uses_recursive_thread_update():
    comment_id, author_id = uuid.uuid4(), uuid.uuid4()
    comment = SimpleNamespace(id=comment_id, user_id=author_id, deleted_at=None)

    class Session:
        committed = False
        statements = []

        def get(self, model, key):
            assert model is Comment and key == comment_id
            return comment

        def execute(self, statement, params):
            self.statements.append((str(statement), params))

        def commit(self):
            self.committed = True

    session = Session()
    post_service.delete_comment(session, comment_id, SimpleNamespace(id=author_id))
    assert session.committed
    assert session.statements[0][1] == {"comment_id": comment_id}
    assert "WITH RECURSIVE thread" in session.statements[0][0]
    assert "child.parent_id = parent.id" in session.statements[0][0]
    assert "AND deleted_at IS NULL" in session.statements[0][0]
    assert "COMMENT_SELF_DELETED" in session.statements[1][0]


def test_only_sender_can_recall_message(monkeypatch):
    conversation_id, message_id, sender_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    message = SimpleNamespace(id=message_id, conversation_id=conversation_id,
                              sender_id=sender_id, deleted_at=None, content="Nội dung cũ")
    monkeypatch.setattr(chat_service, "_member", lambda *_: None)
    monkeypatch.setattr(chat_service, "_ensure_not_blocked", lambda *_: None)
    monkeypatch.setattr(chat_service, "_message", lambda _db, current, _uid: current)

    class Session:
        committed = False

        def get(self, model, key):
            assert model is Message and key == message_id
            return message

        def commit(self):
            self.committed = True

        def refresh(self, _message):
            pass

    session = Session()
    with pytest.raises(HTTPException) as denied:
        chat_service.recall(session, conversation_id, message_id, SimpleNamespace(id=uuid.uuid4()))
    assert denied.value.status_code == 403
    assert not session.committed
    result = chat_service.recall(session, conversation_id, message_id, SimpleNamespace(id=sender_id))
    assert result.deleted_at <= datetime.now(UTC)
    assert result.content is None and session.committed


def test_recalled_message_and_reply_preview_do_not_expose_old_content():
    sender_id, recipient_id, conversation_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    first = Message(id=uuid.uuid4(), conversation_id=conversation_id, sender_id=sender_id,
                    content=None, created_at=datetime.now(UTC), deleted_at=datetime.now(UTC))
    reply = Message(id=uuid.uuid4(), conversation_id=conversation_id, sender_id=recipient_id,
                    content="Trả lời", reply_to_id=first.id, created_at=datetime.now(UTC))
    sender = User(id=sender_id, username="sender")
    recipient = User(id=recipient_id, username="recipient")
    sender_profile = Profile(user_id=sender_id, full_name="Người gửi", avatar_media_id=None)
    recipient_profile = Profile(user_id=recipient_id, full_name="Người nhận", avatar_media_id=None)
    rows = lambda items: SimpleNamespace(all=lambda: items)
    db = Mock()
    db.scalars.side_effect = [rows([first]), rows([sender, recipient]),
                              rows([sender_profile, recipient_profile]), rows([]), rows([])]

    result = chat_service._messages_batch(db, [first, reply], recipient_id)
    assert result[0].isRecalled is True
    assert result[0].content == "Tin nhắn đã được thu hồi"
    assert result[0].attachments == []
    assert result[1].replyTo.isRecalled is True
    assert result[1].replyTo.content == "Tin nhắn đã được thu hồi"


def test_superadmin_open_queue_explicitly_includes_user_reports():
    class Session:
        statement = ""

        def execute(self, statement, _params):
            self.statement = str(statement)
            return _Row()

    session = Session()
    report_service.list_queue(session, SimpleNamespace(system_role=SystemRole.SUPER_ADMIN), "OPEN")
    assert "r.target_type='USER'" in session.statement
    assert "r.status IN ('PENDING','REVIEWING')" in session.statement


def test_deleted_comment_report_closes_without_deleting_again(monkeypatch):
    report_id, target_id, admin_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    report = {"id": report_id, "target_type": "COMMENT", "target_id": target_id,
              "reporter_id": None}
    monkeypatch.setattr(report_service, "_target", lambda *_: None)

    class Session:
        statements = []
        committed = False

        def execute(self, statement, _params):
            sql = str(statement)
            self.statements.append(sql)
            return _Row(report if "SELECT * FROM reports" in sql else None)

        def scalar(self, _statement, _params):
            return None

        def commit(self):
            self.committed = True

    session = Session()
    message = report_service.resolve(session, SimpleNamespace(id=admin_id, system_role=SystemRole.SUPER_ADMIN),
                                     report_id, ReportResolveRequest(decision="RESOLVE", action="HIDE_CONTENT",
                                                                     note="Đã kiểm tra"))
    assert "đã được gỡ" in message
    assert session.committed
    assert not any("UPDATE comments SET" in statement for statement in session.statements)


def test_self_deleted_comment_report_has_specific_notice(monkeypatch):
    report_id, target_id, admin_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    report = {"id": report_id, "target_type": "COMMENT", "target_id": target_id, "reporter_id": None}
    monkeypatch.setattr(report_service, "_target", lambda *_: None)

    class Session:
        def execute(self, statement, _params):
            sql = str(statement)
            if "SELECT * FROM reports" in sql:
                return _Row(report)
            if "COMMENT_SELF_DELETED" in sql:
                return _Row(1)
            return _Row()

        def scalar(self, _statement, _params):
            return None

        def commit(self):
            pass

    notice = report_service.resolve(Session(), SimpleNamespace(id=admin_id, system_role=SystemRole.SUPER_ADMIN),
                                    report_id, ReportResolveRequest(decision="RESOLVE", action="NONE", note="Đã kiểm tra"))
    assert notice == "Bình luận đã được người đăng gỡ trước khi xử lý báo cáo."
