"""Regression coverage for the Test05 moderation and messaging feedback."""

import uuid

from sqlalchemy import text

from src.db.models.user import SystemRole


def _post(client, headers):
    response = client.post("/api/v1/users/me/posts", headers=headers, json={
        "content": "Bài viết kiểm thử phản hồi", "category": "general", "privacy": "public", "media_ids": [],
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _comment(client, headers, post_id, content, parent_id=None):
    payload = {"content": content}
    if parent_id:
        payload["parent_id"] = parent_id
    response = client.post(f"/api/v1/posts/{post_id}/comments", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_removing_parent_comment_hides_all_replies(client, db_session, make_user, auth_headers):
    owner, friend = make_user(name="Chủ bình luận"), make_user(name="Người phản hồi")
    owner_headers, friend_headers = auth_headers(owner), auth_headers(friend)
    post_id = _post(client, owner_headers)
    parent_id = _comment(client, owner_headers, post_id, "Bình luận gốc")
    child_id = _comment(client, friend_headers, post_id, "Phản hồi", parent_id)
    grandchild_id = _comment(client, owner_headers, post_id, "Phản hồi cấp hai", child_id)

    deleted = client.delete(f"/api/v1/posts/comments/{parent_id}", headers=owner_headers)
    assert deleted.status_code == 204, deleted.text
    rows = db_session.execute(text("SELECT id,deleted_at FROM comments WHERE id=ANY(:ids)"), {
        "ids": [uuid.UUID(item) for item in (parent_id, child_id, grandchild_id)],
    }).all()
    assert len(rows) == 3 and all(row.deleted_at is not None for row in rows)
    visible = client.get(f"/api/v1/posts/{post_id}/comments", headers=friend_headers)
    assert visible.status_code == 200 and visible.json() == []


def test_chat_reply_and_recall_are_consistent_for_both_people(client, make_user, auth_headers):
    sender, recipient = make_user(name="Người gửi"), make_user(name="Người nhận")
    sender_headers, recipient_headers = auth_headers(sender), auth_headers(recipient)
    direct = client.post("/api/v1/chat/conversations/direct", headers=sender_headers,
                         json={"target_user_id": str(recipient.id)})
    assert direct.status_code == 200, direct.text
    conversation_id = direct.json()["id"]
    first = client.post(f"/api/v1/chat/conversations/{conversation_id}/messages", headers=sender_headers,
                        json={"content": "Tin gốc"})
    assert first.status_code == 201, first.text
    first_id = first.json()["id"]
    reply = client.post(f"/api/v1/chat/conversations/{conversation_id}/messages", headers=recipient_headers,
                        json={"content": "Tin trả lời", "reply_to_id": first_id})
    assert reply.status_code == 201, reply.text
    assert reply.json()["replyTo"]["content"] == "Tin gốc"

    forbidden = client.delete(f"/api/v1/chat/conversations/{conversation_id}/messages/{first_id}",
                              headers=recipient_headers)
    assert forbidden.status_code == 403
    recalled = client.delete(f"/api/v1/chat/conversations/{conversation_id}/messages/{first_id}",
                             headers=sender_headers)
    assert recalled.status_code == 200, recalled.text
    assert recalled.json()["isRecalled"] is True
    assert recalled.json()["attachments"] == []
    conversation = client.get(f"/api/v1/chat/conversations/{conversation_id}/messages", headers=recipient_headers)
    assert conversation.status_code == 200, conversation.text
    messages = {message["id"]: message for message in conversation.json()}
    assert messages[first_id]["content"] == "Tin nhắn đã được thu hồi"
    assert messages[reply.json()["id"]]["replyTo"]["isRecalled"] is True
    search = client.get(f"/api/v1/chat/conversations/{conversation_id}/messages/search?q=Tin%20g%E1%BB%91c",
                        headers=recipient_headers)
    assert search.status_code == 200 and search.json() == []


def test_user_report_is_in_superadmin_queue_and_removed_comment_closes_safely(
    client, db_session, make_user, auth_headers,
):
    reporter, author = make_user(name="Người báo cáo"), make_user(name="Người bị báo cáo")
    super_admin = make_user(role=SystemRole.SUPER_ADMIN, name="Quản trị hệ thống")
    reporter_headers, author_headers, admin_headers = map(auth_headers, (reporter, author, super_admin))
    post_id = _post(client, author_headers)
    comment_id = _comment(client, author_headers, post_id, "Bình luận sẽ bị gỡ")
    user_report = client.post("/api/v1/reports", headers=reporter_headers, json={
        "target_type": "USER", "target_id": str(author.id), "reason": "Tài khoản có hành vi vi phạm",
    })
    assert user_report.status_code == 201, user_report.text
    duplicate = client.post("/api/v1/reports", headers=reporter_headers, json={
        "target_type": "USER", "target_id": str(author.id), "reason": "Báo cáo trùng",
    })
    assert duplicate.status_code == 409
    comment_report = client.post("/api/v1/reports", headers=reporter_headers, json={
        "target_type": "COMMENT", "target_id": comment_id, "reason": "Bình luận vi phạm",
    })
    assert comment_report.status_code == 201, comment_report.text
    queue = client.get("/api/v1/reports/admin?status=OPEN", headers=admin_headers)
    assert queue.status_code == 200, queue.text
    report_ids = {item["id"] for item in queue.json()}
    assert {user_report.json()["id"], comment_report.json()["id"]}.issubset(report_ids)

    assert client.delete(f"/api/v1/posts/comments/{comment_id}", headers=author_headers).status_code == 204
    detail = client.get(f"/api/v1/reports/admin/{comment_report.json()['id']}", headers=admin_headers)
    assert detail.status_code == 200 and detail.json()["comment"] is None
    decision = client.patch(f"/api/v1/reports/admin/{comment_report.json()['id']}", headers=admin_headers,
                            json={"decision": "RESOLVE", "action": "HIDE_CONTENT", "note": "Đã kiểm tra nội dung"})
    assert decision.status_code == 200, decision.text
    assert "đã được gỡ" in decision.json()["message"]
    assert db_session.scalar(text("SELECT status::text FROM reports WHERE id=:id"),
                             {"id": uuid.UUID(comment_report.json()["id"])}) == "RESOLVED"
