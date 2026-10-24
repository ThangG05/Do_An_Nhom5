"""The batched read paths preserve the public chat and notification payloads."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import event, text

from src.db.models.friendship import FriendRequest, Friendship
from src.db.models.media import MediaFile, MediaStatus
from src.db.models.user import AccountStatus, Profile
from src.db.session import engine
from src.services.friendship_service import list_friends
from src.services.notification_service import header_unread_counts
from src.services.user_service import search_users, serialize_profile


def test_user_search_loads_many_avatars_in_one_batch(db_session, make_user, monkeypatch):
    monkeypatch.setattr("src.services.user_service.create_download_url", lambda media: f"https://r2.test/{media.object_key}")
    viewer = make_user(name="Search viewer")
    expected_ids = set()
    candidates = []
    for number in range(5):
        candidate = make_user(name=f"BatchProbe {number}")
        candidates.append(candidate)
        media_id = uuid.uuid4()
        db_session.add(MediaFile(
            id=media_id, owner_id=candidate.id, bucket="integration-test",
            object_key=f"images/{candidate.id}/{media_id}.jpg", mime_type="image/jpeg",
            file_size=128, status=MediaStatus.READY, uploaded_at=datetime.now(UTC),
        ))
        db_session.get(Profile, candidate.id).avatar_media_id = media_id
        expected_ids.add(str(candidate.id))
    low, high = sorted((viewer.id, candidates[0].id))
    db_session.add(Friendship(user_low_id=low, user_high_id=high))
    db_session.add(FriendRequest(sender_id=viewer.id, receiver_id=candidates[1].id))
    db_session.add(FriendRequest(sender_id=candidates[2].id, receiver_id=viewer.id))
    db_session.commit()
    db_session.refresh(viewer)

    count = 0

    def count_query(*_args):
        nonlocal count
        count += 1

    event.listen(engine, "before_cursor_execute", count_query)
    try:
        results = search_users(db_session, viewer, "BatchProbe")
    finally:
        event.remove(engine, "before_cursor_execute", count_query)

    assert {item.id for item in results} == expected_ids
    assert count == 2
    assert all(item.avatar.startswith("https://r2.test/") for item in results)
    statuses = {item.id: item.friendshipStatus for item in results}
    assert statuses[str(candidates[0].id)] == "friends"
    assert statuses[str(candidates[1].id)] == "pending_sent"
    assert statuses[str(candidates[2].id)] == "pending_received"
    assert all(statuses[str(candidate.id)] == "none" for candidate in candidates[3:])


def test_user_search_includes_viewers_own_profile(db_session, make_user):
    viewer = make_user(name="Nguyen Manh Thang")
    results = search_users(db_session, viewer, "Nguyen Manh Thang")
    own = next(item for item in results if item.id == str(viewer.id))
    assert own.friendshipStatus == "self"


def test_user_search_uses_current_name_and_finds_disabled_friend(db_session, make_user):
    viewer = make_user(name="Search friend viewer")
    friend = make_user(name="Previous profile name")
    outsider = make_user(name="Other disabled account")
    low, high = sorted((viewer.id, friend.id))
    db_session.add(Friendship(user_low_id=low, user_high_id=high))
    db_session.get(Profile, friend.id).full_name = "Hoa Son Quy"
    friend.status = AccountStatus.DISABLED
    outsider.status = AccountStatus.DISABLED
    db_session.flush()

    result = search_users(db_session, viewer, "Hoa Son Quy")
    assert [(item.id, item.name, item.accountStatus) for item in result] == [
        (str(friend.id), "Hoa Son Quy", "DISABLED")
    ]
    assert all(item.id != str(friend.id) for item in search_users(db_session, viewer, "Previous profile name"))
    assert all(item.id != str(outsider.id) for item in search_users(db_session, viewer, "Other disabled account"))


def test_friends_list_batches_mutual_counts(db_session, make_user):
    viewer = make_user(name="Friend list viewer")
    first = make_user(name="Friend list first")
    second = make_user(name="Friend list second")
    for left, right in ((viewer.id, first.id), (viewer.id, second.id), (first.id, second.id)):
        low, high = sorted((left, right))
        db_session.add(Friendship(user_low_id=low, user_high_id=high))
    db_session.commit()
    db_session.refresh(viewer)

    count = 0

    def count_query(*_args):
        nonlocal count
        count += 1

    event.listen(engine, "before_cursor_execute", count_query)
    try:
        friends = list_friends(db_session, viewer, viewer)
    finally:
        event.remove(engine, "before_cursor_execute", count_query)

    assert {item.id for item in friends} == {str(first.id), str(second.id)}
    assert all(item.mutualCount == 1 for item in friends)
    assert count == 3


def test_profile_friend_count_matches_visible_list(db_session, make_user):
    owner = make_user(name="Profile owner")
    visible = make_user(name="Visible friend")
    disabled = make_user(name="Disabled friend")
    blocked = make_user(name="Blocked friend")
    for friend in (visible, disabled, blocked):
        low, high = sorted((owner.id, friend.id))
        db_session.add(Friendship(user_low_id=low, user_high_id=high))
    disabled.status = AccountStatus.DISABLED
    db_session.flush()
    db_session.execute(text("INSERT INTO user_blocks(blocker_id, blocked_id) VALUES (:owner, :friend)"),
                       {"owner": owner.id, "friend": blocked.id})
    db_session.flush()

    friends = list_friends(db_session, owner, owner)
    profile = serialize_profile(db_session, owner, owner.id)

    assert {friend.id for friend in friends} == {str(visible.id), str(disabled.id)}
    assert next(friend for friend in friends if friend.id == str(disabled.id)).accountStatus == "DISABLED"
    assert profile.friendsCount == len(friends) == 2
    assert str(owner.id) in {friend.id for friend in list_friends(db_session, disabled, owner)}


def test_chat_and_notification_read_paths(client, make_user, auth_headers, db_session, monkeypatch):
    author = make_user(name="Người gửi")
    friend = make_user(name="Người nhận")
    monkeypatch.setattr("src.services.chat_service.create_download_url", lambda media: f"https://r2.test/{media.object_key}")
    avatar_id = uuid.uuid4()
    db_session.add(MediaFile(
        id=avatar_id, owner_id=author.id, bucket="integration-test",
        object_key=f"images/{author.id}/{avatar_id}.jpg", mime_type="image/jpeg",
        file_size=128, status=MediaStatus.READY, uploaded_at=datetime.now(UTC),
    ))
    db_session.get(Profile, author.id).avatar_media_id = avatar_id
    db_session.commit()
    author_headers = auth_headers(author)
    friend_headers = auth_headers(friend)

    direct = client.post("/api/v1/chat/conversations/direct", headers=author_headers,
                         json={"target_user_id": str(friend.id)})
    assert direct.status_code == 200, direct.text
    conversation_id = direct.json()["id"]
    for content in ("Tin nhắn thứ nhất", "Tin nhắn thứ hai"):
        sent = client.post(f"/api/v1/chat/conversations/{conversation_id}/messages",
                           headers=author_headers, json={"content": content, "media_ids": []})
        assert sent.status_code == 201, sent.text

    inbox = client.get("/api/v1/chat/conversations", headers=friend_headers)
    assert inbox.status_code == 200, inbox.text
    assert inbox.json()[0]["participantName"] == "Người gửi"
    assert inbox.json()[0]["participantAvatar"] == f"https://r2.test/images/{author.id}/{avatar_id}.jpg"
    assert inbox.json()[0]["unreadCount"] == 2
    messages = client.get(f"/api/v1/chat/conversations/{conversation_id}/messages",
                          headers=friend_headers)
    assert messages.status_code == 200, messages.text
    assert {item["content"] for item in messages.json()} == {"Tin nhắn thứ nhất", "Tin nhắn thứ hai"}
    assert all(item["senderName"] == "Người gửi" for item in messages.json())
    assert all(item["status"] == "seen" for item in messages.json())

    post = client.post("/api/v1/users/me/posts", headers=author_headers,
                       json={"content": "Bài viết thử thông báo", "privacy": "public",
                             "category": "general", "media_ids": []})
    assert post.status_code == 201, post.text
    commented = client.post(f"/api/v1/posts/{post.json()['id']}/comments",
                            headers=friend_headers, json={"content": "Bình luận thử"})
    assert commented.status_code == 201, commented.text
    thread = client.get(f"/api/v1/posts/{post.json()['id']}/comments", headers=author_headers)
    assert thread.status_code == 200, thread.text
    assert thread.json()[0]["id"] == commented.json()["id"]
    detail = client.get(f"/api/v1/posts/{post.json()['id']}", headers=author_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["comments"][0]["id"] == commented.json()["id"]
    liked = client.put(f"/api/v1/posts/{post.json()['id']}/like",
                       headers=friend_headers, json={"is_liked": True})
    assert liked.status_code == 200, liked.text
    feed = client.get("/api/v1/posts/feed?limit=10", headers=friend_headers)
    assert feed.status_code == 200, feed.text
    card = next(item for item in feed.json() if item["id"] == post.json()["id"])
    assert card["commentsCount"] == 1
    assert card["comments"][0]["id"] == commented.json()["id"]
    assert card["likesCount"] == 1 and card["isLiked"] is True
    notifications = client.get("/api/v1/notifications", headers=author_headers)
    assert notifications.status_code == 200, notifications.text
    comment_items = [item for item in notifications.json()["items"] if item["type"] == "COMMENT"
                     and item["reference_id"] == post.json()["id"]]
    assert comment_items
    assert comment_items[0]["actor_name"] == "Người nhận"
    assert comment_items[0]["payload"]["comment_id"] == commented.json()["id"]

    sent_again = client.post(f"/api/v1/chat/conversations/{conversation_id}/messages",
                             headers=author_headers, json={"content": "Tin nhắn chưa đọc", "media_ids": []})
    assert sent_again.status_code == 201, sent_again.text
    header = client.get("/api/v1/notifications/header-counts", headers=friend_headers)
    message_count = client.get("/api/v1/chat/unread-count", headers=friend_headers)
    notification_count = client.get("/api/v1/notifications/unread-count", headers=friend_headers)
    assert header.status_code == message_count.status_code == notification_count.status_code == 200
    assert header.json() == {
        "messages": message_count.json()["unread_count"],
        "notifications": notification_count.json()["unread_count"],
    }
    assert header.json()["messages"] == 1

    statements = 0

    def count_query(*_args):
        nonlocal statements
        statements += 1

    friend_id = friend.id
    event.listen(engine, "before_cursor_execute", count_query)
    try:
        assert header_unread_counts(db_session, friend_id) == (header.json()["notifications"], 1)
    finally:
        event.remove(engine, "before_cursor_execute", count_query)
    assert statements == 1
