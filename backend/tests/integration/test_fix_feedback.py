import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from src.api.endpoints import locations
from src.db.models.media import MediaFile, MediaStatus
from src.db.models.post import Post, PostStatus, PostType, PostVisibility


def test_search_matches_vietnamese_name_without_accents(client, make_user, auth_headers):
    viewer = make_user(name="Người tìm kiếm")
    person = make_user(name="Nguyễn Mạnh Thắng")
    response = client.get("/api/v1/users/search?q=thang", headers=auth_headers(viewer))
    assert response.status_code == 200, response.text
    assert str(person.id) in {item["id"] for item in response.json()}


def test_blocked_list_uses_real_avatar(client, db_session, make_user, auth_headers):
    viewer = make_user(name="Người chặn")
    blocked = make_user(name="Người bị chặn")
    media_id = uuid.uuid4()
    db_session.add(MediaFile(
        id=media_id, owner_id=blocked.id, bucket="integration-test",
        object_key=f"images/users/{blocked.id}/avatar/{media_id}.jpg",
        original_name="avatar.jpg", mime_type="image/jpeg", file_size=128,
        status=MediaStatus.READY, uploaded_at=datetime.now(UTC),
    ))
    blocked.profile.avatar_media_id = media_id
    db_session.commit()
    headers = auth_headers(viewer)
    assert client.put(f"/api/v1/users/{blocked.id}/block", headers=headers).status_code == 200
    response = client.get("/api/v1/users/me/blocked", headers=headers)
    assert response.status_code == 200, response.text
    entry = next(item for item in response.json() if item["id"] == str(blocked.id))
    assert entry["avatar"].startswith("https://r2.test/")


def test_legacy_category_post_cannot_bypass_group_membership(client, db_session, make_user, auth_headers):
    author = make_user(name="Tác giả cũ")
    outsider = make_user(name="Người chưa vào nhóm")
    legacy = Post(author_id=author.id, content="Bài Pass đồ cũ", category="market",
                  post_type=PostType.PROFILE_POST, visibility=PostVisibility.PUBLIC,
                  status=PostStatus.APPROVED)
    db_session.add(legacy)
    db_session.commit()
    headers = auth_headers(outsider)
    assert str(legacy.id) not in {item["id"] for item in client.get("/api/v1/posts/feed", headers=headers).json()}
    assert client.get(f"/api/v1/posts/{legacy.id}", headers=headers).status_code == 403
    assert str(legacy.id) not in {item["id"] for item in client.get(f"/api/v1/users/{author.id}/posts", headers=headers).json()}


def test_reverse_location_uses_address_and_rejects_distant_match(client, make_user, auth_headers, monkeypatch):
    viewer = make_user()

    async def nearby(_path, _params):
        return {"features": [{"geometry": {"coordinates": [105.8, 21.0]},
                              "properties": {"housenumber": "12", "street": "Chùa Bộc",
                                             "city": "Hà Nội", "country": "Việt Nam"}}]}

    monkeypatch.setattr(locations, "_photon_get", nearby)
    url = "/api/v1/locations/reverse?latitude=21&longitude=105.8"
    response = client.get(url, headers=auth_headers(viewer))
    assert response.status_code == 200, response.text
    assert response.json()["name"].startswith("12 Chùa Bộc")

    async def distant(_path, _params):
        return {"features": [{"geometry": {"coordinates": [106.0, 21.0]},
                              "properties": {"street": "Đường khác", "city": "Hà Nội"}}]}

    monkeypatch.setattr(locations, "_photon_get", distant)
    assert client.get(url, headers=auth_headers(viewer)).json() is None


def test_study_post_does_not_keep_location(client, db_session, make_user, auth_headers):
    group_id = db_session.execute(text("SELECT id FROM groups WHERE slug='hoc-tap' AND status='ACTIVE'")).scalar_one_or_none()
    if group_id is None:
        pytest.skip("Chưa có nhóm Học tập.")
    author = make_user(name="Người chia sẻ tài liệu")
    db_session.execute(text("INSERT INTO group_members(group_id,user_id,role) VALUES(:gid,:uid,'MEMBER')"),
                       {"gid": group_id, "uid": author.id})
    db_session.commit()
    response = client.post("/api/v1/users/me/posts", headers=auth_headers(author), json={
        "form_version": 2, "category": "study", "content": "Giới thiệu tài liệu môn học",
        "studyListing": {"subjectName": "Giải tích 1"},
        "location": {"name": "Vị trí hiện tại", "latitude": 21.0, "longitude": 105.8},
    })
    assert response.status_code == 201, response.text
    assert response.json()["location"] is None
