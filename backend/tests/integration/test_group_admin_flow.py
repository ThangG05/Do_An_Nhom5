import uuid

from sqlalchemy import text


def test_group_join_moderation_and_group_admin_permissions(client, db_session, make_user, auth_headers, active_group):
    member = make_user(name="Thành viên nhóm")
    admin = make_user(name="Quản trị nhóm")
    outsider = make_user(name="Người ngoài nhóm")
    group_id = active_group["id"]
    db_session.execute(text("INSERT INTO group_members(group_id,user_id,role) VALUES(:gid,:uid,'ADMIN')"), {"gid": group_id, "uid": admin.id})
    db_session.commit()

    join = client.post(f"/api/v1/groups/{group_id}/join", headers=auth_headers(member))
    assert join.status_code == 200
    request_id = db_session.execute(text("SELECT id FROM group_join_requests WHERE group_id=:gid AND user_id=:uid"), {"gid": group_id, "uid": member.id}).scalar_one()

    forbidden = client.get(f"/api/v1/groups/{group_id}/admin/join-requests", headers=auth_headers(outsider))
    assert forbidden.status_code == 403
    queue = client.get(f"/api/v1/groups/{group_id}/admin/join-requests", headers=auth_headers(admin))
    assert queue.status_code == 200
    assert any(item["id"] == str(request_id) for item in queue.json())

    approved_member = client.patch(
        f"/api/v1/groups/{group_id}/admin/join-requests/{request_id}",
        headers=auth_headers(admin),
        json={"decision": "APPROVE"},
    )
    assert approved_member.status_code == 204

    created = client.post(
        f"/api/v1/groups/{group_id}/posts",
        headers=auth_headers(member),
        json={"content": "Bài chờ Group Admin duyệt", "media_ids": []},
    )
    assert created.status_code == 201, created.text
    post_id = created.json()["id"]
    assert created.json()["status"] == "PENDING"

    pending = client.get(f"/api/v1/groups/{group_id}/admin/posts/pending", headers=auth_headers(admin))
    assert pending.status_code == 200
    assert any(item["id"] == post_id for item in pending.json())
    moderated = client.patch(
        f"/api/v1/groups/{group_id}/admin/posts/{post_id}/moderate",
        headers=auth_headers(admin),
        json={"decision": "APPROVE"},
    )
    assert moderated.status_code == 200
    assert moderated.json()["status"] == "APPROVED"
    assert client.put(f"/api/v1/groups/{group_id}/admin/posts/{post_id}/pin", headers=auth_headers(admin), json={"is_pinned": True}).status_code == 204

    feed = client.get(f"/api/v1/groups/{group_id}/posts?sort=pinned", headers=auth_headers(member))
    assert feed.status_code == 200
    assert feed.json()[0]["id"] == post_id and feed.json()[0]["isPinned"] is True
    assert db_session.execute(text("SELECT role FROM group_members WHERE group_id=:gid AND user_id=:uid"), {"gid": group_id, "uid": member.id}).scalar_one() == "MEMBER"
