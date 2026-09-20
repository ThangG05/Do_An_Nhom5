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

    users = client.get(f"/api/v1/admin/users?q={target.username}", headers=admin_headers)
    assert users.status_code == 200
    assert users.json()["total"] == 1
    assert users.json()["items"][0]["id"] == str(target.id)

    grant = client.put(
        f"/api/v1/admin/users/{target.id}/group-admin",
        headers=admin_headers,
        json={"group_id": str(active_group["id"]), "grant": True},
    )
    assert grant.status_code == 204
    assert client.get(f"/api/v1/groups/{active_group['id']}/admin/members", headers=auth_headers(target)).status_code == 200

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
