import uuid

from sqlalchemy import text

from src.db.models.user import SystemRole


def test_super_admin_dashboard_account_role_and_audit_flow(client, db_session, make_user, auth_headers, active_group):
    super_admin = make_user(role=SystemRole.SUPER_ADMIN, name="Super Admin kiểm thử")
    target = make_user(name="Tài khoản được quản lý")
    regular = make_user(name="Người dùng thường")
    admin_headers = auth_headers(super_admin)

    assert client.get("/api/v1/admin/dashboard", headers=auth_headers(regular)).status_code == 403
    dashboard = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_users"] >= 3
    assert dashboard.json()["total_users"] == db_session.scalar(text("SELECT count(*) FROM users WHERE deleted_at IS NULL"))

    users = client.get(f"/api/v1/admin/users?q={target.username}", headers=admin_headers)
    assert users.status_code == 200
    assert users.json()["total"] == 1
    assert users.json()["items"][0]["id"] == str(target.id)

    request_id = uuid.uuid4()
    for index, counts in enumerate(((10, 4, 14, "provider"), (None, None, None, "missing")), 1):
        db_session.execute(text("""
            INSERT INTO rag_token_usage(user_id,request_id,call_index,provider,model,
                                        input_tokens,output_tokens,total_tokens,usage_source,status)
            VALUES(:uid,:rid,:idx,'gemini','gemini-test',:input,:output,:total,:source,'SUCCESS')
        """), {"uid": target.id, "rid": request_id, "idx": index,
               "input": counts[0], "output": counts[1], "total": counts[2], "source": counts[3]})
    db_session.commit()
    usage_list = client.get(f"/api/v1/admin/users?q={target.username}&period=all", headers=admin_headers)
    assert usage_list.status_code == 200, usage_list.text
    assert usage_list.json()["items"][0]["rag_total_tokens"] == 14
    detail_url = f"/api/v1/admin/users/{target.id}/rag-usage?period=all"
    assert client.get(detail_url, headers=auth_headers(regular)).status_code == 403
    detail = client.get(detail_url, headers=admin_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["usage_calls"] == 2
    assert detail.json()["usage_missing"] == 1
    assert detail.json()["input_tokens"] == 10

    for _ in range(11):
        db_session.execute(text("""
            INSERT INTO rag_token_usage(user_id,request_id,call_index,provider,model,
                                        input_tokens,output_tokens,total_tokens,usage_source,status)
            VALUES(:uid,:rid,1,'gemini','gemini-test',1,1,2,'provider','SUCCESS')
        """), {"uid": target.id, "rid": uuid.uuid4()})
    db_session.commit()
    first_page = client.get(detail_url, headers=admin_headers)
    second_page = client.get(f"{detail_url}&offset=10", headers=admin_headers)
    assert first_page.status_code == second_page.status_code == 200
    assert first_page.json()["usage_calls"] == second_page.json()["usage_calls"] == 13
    assert len(first_page.json()["calls"]) == 10
    assert len(second_page.json()["calls"]) == 3
    assert {call["id"] for call in first_page.json()["calls"]}.isdisjoint(
        call["id"] for call in second_page.json()["calls"])
    assert client.get(f"{detail_url}&offset=-1", headers=admin_headers).status_code == 422

    grant = client.put(
        f"/api/v1/admin/users/{target.id}/group-admin",
        headers=admin_headers,
        json={"group_id": str(active_group["id"]), "grant": True},
    )
    assert grant.status_code == 204
    assert client.get(f"/api/v1/groups/{active_group['id']}/admin/members", headers=auth_headers(target)).status_code == 200
    assigned = client.get(f"/api/v1/admin/users?q={target.username}", headers=admin_headers)
    assert assigned.status_code == 200
    assert any(group["id"] == str(active_group["id"]) for group in assigned.json()["items"][0]["admin_groups"])

    group_admin_url = f"/api/v1/admin/groups/{active_group['id']}/admins"
    assert client.get(group_admin_url, headers=auth_headers(regular)).status_code == 403
    group_admins = client.get(group_admin_url, headers=admin_headers)
    assert group_admins.status_code == 200, group_admins.text
    assert any(item["id"] == str(target.id) and item["email"] == target.email
               for item in group_admins.json())

    warning = client.post(
        f"/api/v1/admin/users/{target.id}/discipline",
        headers=admin_headers,
        json={"action": "WARN", "reason": "Kiểm thử cảnh báo tích hợp"},
    )
    assert warning.status_code == 204
    assert db_session.execute(text("SELECT warning_count FROM users WHERE id=:uid"), {"uid": target.id}).scalar_one() == 1

    locked = client.patch(
        f"/api/v1/admin/users/{target.id}/status",
        headers=admin_headers,
        json={"status": "LOCKED", "reason": "Kiểm thử khóa tài khoản"},
    )
    assert locked.status_code == 204
    assert client.get("/api/v1/users/me", headers=auth_headers(target)).status_code == 403

    audit = client.get("/api/v1/admin/audit-logs?limit=20", headers=admin_headers)
    assert audit.status_code == 200
    actions = {item["action"] for item in audit.json() if item["target_id"] == str(target.id)}
    assert {"GROUP_ADMIN_GRANTED", "USER_WARN", "ACCOUNT_STATUS_CHANGED"}.issubset(actions)
    assert client.patch(f"/api/v1/admin/users/{super_admin.id}/status", headers=admin_headers, json={"status": "LOCKED", "reason": "Không được phép"}).status_code == 403
