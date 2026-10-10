from sqlalchemy import text


def test_group_category_post_requires_membership_and_review(client, db_session, make_user, auth_headers):
    author = make_user(name="Sinh viên đăng Pass đồ")
    group_id = db_session.execute(text("SELECT id FROM groups WHERE slug='pass-do' AND status='ACTIVE'")).scalar_one()
    payload = {"content": "Bán sách cũ", "category": "market", "privacy": "private", "media_ids": [], "marketListing": {"price": "50000"}}

    denied = client.post("/api/v1/users/me/posts", headers=auth_headers(author), json=payload)
    assert denied.status_code == 403

    db_session.execute(text("INSERT INTO group_members(group_id,user_id,role) VALUES(:gid,:uid,'MEMBER')"), {"gid": group_id, "uid": author.id})
    db_session.commit()
    created = client.post("/api/v1/users/me/posts", headers=auth_headers(author), json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["groupId"] == str(group_id)
    assert created.json()["status"] == "PENDING"
    assert created.json()["privacy"] == "public"


def test_direct_chat_can_start_from_non_friend_profile(client, make_user, auth_headers):
    sender = make_user(name="Người gửi")
    recipient = make_user(name="Người nhận")
    response = client.post("/api/v1/chat/conversations/direct", headers=auth_headers(sender), json={"target_user_id": str(recipient.id)})
    assert response.status_code == 200, response.text
    assert response.json()["participantId"] == str(recipient.id)
