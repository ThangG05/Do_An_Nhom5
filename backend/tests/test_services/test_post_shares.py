import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from src.db.models.post import PostShare, PostStatus
from src.models.post import RegisterPostShareRequest
from src.services.post_service import _contains_post_link, register_share


def test_share_link_matches_only_the_selected_post() -> None:
    source_id = uuid.uuid4()
    other_id = uuid.uuid4()
    assert _contains_post_link(f"Xem https://example.edu/posts/{source_id}", source_id)
    assert not _contains_post_link(f"https://example.edu/posts/{source_id}xyz", source_id)
    assert not _contains_post_link(f"https://example.edu/posts/{other_id}", source_id)


def test_register_share_rejects_another_users_post() -> None:
    actor = SimpleNamespace(id=uuid.uuid4())
    source_id, destination_id = uuid.uuid4(), uuid.uuid4()
    db = Mock()
    db.get.return_value = SimpleNamespace(
        author_id=uuid.uuid4(), deleted_at=None, status=PostStatus.APPROVED,
        group_id=None, content=f"https://example.edu/posts/{source_id}",
    )
    with patch("src.services.post_service.get_visible_post"):
        with pytest.raises(HTTPException) as error:
            register_share(db, source_id, actor, RegisterPostShareRequest(
                destination_type="POST", destination_id=destination_id,
            ))
    assert error.value.status_code == 400
    db.execute.assert_not_called()


def test_post_share_metadata_has_unique_destination() -> None:
    table = PostShare.__table__
    assert {"post_id", "actor_id", "destination_type", "destination_id"} <= set(table.columns.keys())
    assert any(set(constraint.columns.keys()) == {"destination_type", "destination_id"}
               for constraint in table.constraints)
