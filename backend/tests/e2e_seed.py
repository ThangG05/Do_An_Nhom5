"""Seed and remove browser-test identities without touching normal project data."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from src.core.security import hash_password
from src.db.models.post import Post, PostStatus, PostType, PostVisibility
from src.db.models.user import AccountStatus, Profile, SystemRole, User
from src.db.session import SessionLocal

PASSWORD = "E2ePassword123!"
EMAILS = {
    "user": "e2e-user@hvnh.edu.vn",
    "group_admin": "e2e-group-admin@hvnh.edu.vn",
    "member": "e2e-member@hvnh.edu.vn",
    "super_admin": "e2e-super-admin@hvnh.edu.vn",
    "target": "e2e-target@hvnh.edu.vn",
}


def cleanup(db) -> None:
    ids = list(db.scalars(text("SELECT id FROM users WHERE email LIKE 'e2e-%@hvnh.edu.vn'")))
    if not ids:
        return
    db.execute(text("DELETE FROM audit_logs WHERE actor_id = ANY(:ids) OR target_id = ANY(:ids)"), {"ids": ids})
    # The deployed schema deliberately RESTRICTs deleting post authors so that
    # application code cannot accidentally erase content. E2E owns these posts,
    # therefore it removes them explicitly before removing its identities.
    db.execute(text("DELETE FROM posts WHERE author_id = ANY(:ids)"), {"ids": ids})
    db.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": ids})
    db.commit()


def add_user(db, key: str, name: str, role: SystemRole = SystemRole.USER) -> User:
    user = User(
        id=uuid.uuid4(),
        email=EMAILS[key],
        username=f"e2e_{key}",
        password_hash=hash_password(PASSWORD),
        status=AccountStatus.ACTIVE,
        system_role=role,
    )
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, full_name=name, student_code=f"E2E-{key.upper()}", social_links={}))
    return user


def setup(db) -> dict:
    cleanup(db)
    group = db.execute(text("SELECT id,name,slug FROM groups WHERE status='ACTIVE' ORDER BY name LIMIT 1")).mappings().first()
    if group is None:
        raise RuntimeError("Cần ít nhất một nhóm ACTIVE để chạy E2E.")
    users = {
        "user": add_user(db, "user", "E2E User"),
        "group_admin": add_user(db, "group_admin", "E2E Group Admin"),
        "member": add_user(db, "member", "E2E Member"),
        "super_admin": add_user(db, "super_admin", "E2E Super Admin", SystemRole.SUPER_ADMIN),
        "target": add_user(db, "target", "E2E Managed User"),
    }
    db.flush()
    db.execute(text("INSERT INTO group_members(group_id,user_id,role) VALUES(:gid,:admin,'ADMIN'),(:gid,:member,'MEMBER')"), {"gid": group["id"], "admin": users["group_admin"].id, "member": users["member"].id})
    pending = Post(
        group_id=group["id"], author_id=users["member"].id,
        content="E2E bài viết đang chờ duyệt", category="general",
        post_type=PostType.STANDARD, visibility=PostVisibility.PUBLIC, status=PostStatus.PENDING,
    )
    db.add(pending)
    db.commit()
    return {
        "password": PASSWORD,
        "emails": EMAILS,
        "group": {"id": str(group["id"]), "name": group["name"], "slug": group["slug"]},
        "pending_post_id": str(pending.id),
    }


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "setup"
    with SessionLocal() as db:
        if action == "cleanup":
            cleanup(db)
            print(json.dumps({"cleaned": True}))
        else:
            print(json.dumps(setup(db)))


if __name__ == "__main__":
    main()
