import uuid
from datetime import UTC, datetime

from sqlalchemy import text

from src.db.models.media import MediaFile, MediaStatus


def test_user_profile_post_photo_listing_and_social_flow(client, db_session, make_user, auth_headers):
    password = "Integration123!"
    user = make_user(name="Người dùng kiểm thử", password=password)
    friend = make_user(name="Bạn kiểm thử")
    headers = auth_headers(user)
    friend_headers = auth_headers(friend)

    assert client.get("/api/v1/users/me").status_code == 401
    login = client.post("/api/v1/auth/login", json={"email": user.email, "password": password})
    assert login.status_code == 200
    assert login.json()["user"]["id"] == str(user.id)
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    profile = client.get("/api/v1/users/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["name"] == "Người dùng kiểm thử"

    updated = client.patch("/api/v1/users/me", headers=headers, json={"bio": "Hồ sơ tích hợp", "faculty": "Công nghệ thông tin"})
    assert updated.status_code == 200
    assert updated.json()["bio"] == "Hồ sơ tích hợp"

    media_id = uuid.uuid4()
    db_session.add(MediaFile(
        id=media_id,
        owner_id=user.id,
        bucket="integration-test",
        object_key=f"images/users/{user.id}/posts/{media_id}.jpg",
        original_name="photo.jpg",
        mime_type="image/jpeg",
        file_size=128,
        status=MediaStatus.READY,
        uploaded_at=datetime.now(UTC),
    ))
    db_session.commit()

    created = client.post("/api/v1/users/me/posts", headers=headers, json={
        "content": "Bán giáo trình kiểm thử",
        "privacy": "public",
        "category": "market",
        "media_ids": [str(media_id)],
        "marketListing": {"price": "100.000đ", "condition": "Mới", "location": "HVNH", "status": "active"},
    })
    assert created.status_code == 201, created.text
    post = created.json()
    assert post["marketListing"]["price"] == "100.000đ"
    assert post["media"][0]["url"].startswith("https://r2.test/")

    photos = client.get(f"/api/v1/users/{user.id}/photos", headers=friend_headers)
    assert photos.status_code == 200
    assert photos.json()[0]["id"] == str(media_id)

    listings = client.get(f"/api/v1/users/{user.id}/listings?category=market", headers=friend_headers)
    assert listings.status_code == 200
    assert listings.json()[0]["price"] == "100.000đ"
    assert listings.json()[0]["location"] == "HVNH"

    liked = client.put(f"/api/v1/posts/{post['id']}/like", headers=friend_headers, json={"is_liked": True})
    assert liked.status_code == 200
    assert liked.json() == {"isLiked": True, "likesCount": 1}
    comment = client.post(f"/api/v1/posts/{post['id']}/comments", headers=friend_headers, json={"content": "Tôi quan tâm"})
    assert comment.status_code == 201

    blocked = client.put(f"/api/v1/users/{friend.id}/block", headers=headers)
    assert blocked.status_code == 200 and blocked.json()["blocked"] is True
    assert client.get(f"/api/v1/users/{user.id}", headers=friend_headers).status_code == 403
    assert db_session.execute(text("SELECT count(*) FROM post_likes WHERE post_id=:pid"), {"pid": uuid.UUID(post["id"])}).scalar_one() == 1
