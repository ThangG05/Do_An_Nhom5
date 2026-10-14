import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

from src.db.models.chat import Message
from src.db.models.notification import Notification, NotificationType
from src.db.models.post import Comment
from src.db.models.user import Profile, User
from src.models.system import MaintenanceResponse
from src.services.chat_service import _messages_batch
from src.services.maintenance_cache import MaintenanceCache
from src.services.notification_service import _serialize_many
from src.services.post_service import _comment_responses


def _rows(items):
    return SimpleNamespace(all=lambda: items)


def test_maintenance_snapshot_coalesces_parallel_reads_and_invalidates():
    calls = []

    def load():
        calls.append(1)
        return MaintenanceResponse(enabled=False)

    cache = MaintenanceCache(load, ttl_seconds=60)

    async def check():
        await asyncio.gather(*(cache.get() for _ in range(20)))
        assert len(calls) == 1
        cache.invalidate()
        await cache.get()
        assert len(calls) == 2

    asyncio.run(check())


def test_notification_list_batches_actor_and_legacy_comment_lookups():
    actor_id, post_id, comment_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    actor = User(id=actor_id, username="student")
    profile = Profile(user_id=actor_id, full_name="Sinh viên", avatar_media_id=None)
    items = [Notification(
        id=uuid.uuid4(), user_id=uuid.uuid4(), actor_id=actor_id,
        type=NotificationType.COMMENT, title="Bình luận", payload={},
        reference_type="POST", reference_id=post_id,
        created_at=datetime.now(UTC), read_at=None,
    ) for _ in range(20)]
    db = Mock()
    db.scalars.side_effect = [_rows([actor]), _rows([profile])]
    db.execute.return_value = _rows([(post_id, actor_id, comment_id)])

    result = _serialize_many(db, items)

    assert len(result) == 20
    assert all(item.payload["comment_id"] == str(comment_id) for item in result)
    assert all(item.actor_name == "Sinh viên" for item in result)
    assert db.scalars.call_count == 2
    assert db.execute.call_count == 1


def test_message_cards_batch_sender_and_receipt_lookups():
    sender_id, conversation_id = uuid.uuid4(), uuid.uuid4()
    sender = User(id=sender_id, username="student")
    profile = Profile(user_id=sender_id, full_name="Sinh viên", avatar_media_id=None)
    items = [Message(
        id=uuid.uuid4(), conversation_id=conversation_id, sender_id=sender_id,
        content="Xin chào", created_at=datetime.now(UTC), deleted_at=None,
    ) for _ in range(50)]
    db = Mock()
    db.scalars.side_effect = [_rows([sender]), _rows([profile]), _rows([]), _rows([])]

    result = _messages_batch(db, items, sender_id)

    assert len(result) == 50
    assert all(item.senderName == "Sinh viên" and item.status == "sent" for item in result)
    assert db.scalars.call_count == 4


def test_comment_thread_batches_authors():
    author_id, post_id = uuid.uuid4(), uuid.uuid4()
    author = User(id=author_id, username="commenter")
    profile = Profile(user_id=author_id, full_name="Commenter", avatar_media_id=None)
    comments = [Comment(
        id=uuid.uuid4(), post_id=post_id, user_id=author_id,
        content="Hello", created_at=datetime.now(UTC),
    ) for _ in range(50)]
    db = Mock()
    db.execute.return_value = _rows([(author, profile)])

    result = _comment_responses(db, comments)

    assert len(result) == 50
    assert all(item.author.name == "Commenter" for item in result)
    assert db.execute.call_count == 1
    db.scalars.assert_not_called()
