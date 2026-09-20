import uuid

import pytest

from src.services.storage_service import MediaKind, build_object_key


@pytest.mark.parametrize(
    ("kind", "purpose", "extension", "prefix"),
    [
        (MediaKind.IMAGE, "avatars", "webp", "images/"),
        (MediaKind.SHORT_VIDEO, "posts", "mp4", "short-videos/"),
        (MediaKind.AUDIO, "messages", "mp3", "audio/"),
    ],
)
def test_build_object_key_uses_expected_root(kind, purpose, extension, prefix):
    owner_id, media_id = uuid.uuid4(), uuid.uuid4()
    key = build_object_key(kind, owner_id, purpose, media_id, extension)
    assert key == f"{prefix}users/{owner_id}/{purpose}/{media_id}.{extension}"


def test_build_object_key_rejects_unsafe_purpose():
    with pytest.raises(ValueError):
        build_object_key(MediaKind.IMAGE, uuid.uuid4(), "../avatars", uuid.uuid4(), "jpg")
