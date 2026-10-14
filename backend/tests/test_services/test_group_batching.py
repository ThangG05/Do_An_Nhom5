import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.services import group_service


def test_group_post_lists_use_one_batched_serializer():
    db = Mock()
    posts = [SimpleNamespace(id=uuid.uuid4()) for _ in range(12)]
    db.scalars.return_value.all.return_value = posts
    group_id = uuid.uuid4()
    user = SimpleNamespace(id=uuid.uuid4())

    with (
        patch.object(group_service, "_group"),
        patch.object(group_service, "_require_reader"),
        patch.object(group_service, "_serialize_feed_posts", return_value=["batch"]) as serialize,
    ):
        assert group_service.list_posts(db, group_id, user) == ["batch"]
        assert group_service.list_my_posts(db, group_id, user) == ["batch"]

    assert serialize.call_count == 2
    assert all(call.args == (db, posts, user.id) for call in serialize.call_args_list)
