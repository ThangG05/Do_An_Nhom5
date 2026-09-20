"""Provision one super admin and one dedicated admin for every active group.

Passwords are generated once and only their Argon2 hashes are stored. Existing
accounts are never assigned a new password by rerunning this script.
"""
import json
import re
import secrets
import string
from datetime import UTC, datetime

from sqlalchemy import text

from src.core.security import hash_password
from src.db.models.user import AccountStatus, Profile, SystemRole, User
from src.db.session import SessionLocal

CANONICAL_GROUP_SLUGS = ("pass-do", "ghep-phong-tim-tro", "su-kien", "hoc-tap")


def password() -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%_-"
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(22))
        if any(c.islower() for c in value) and any(c.isupper() for c in value) and any(c.isdigit() for c in value):
            return value


def local_name(slug: str) -> str:
    value = re.sub(r"[^a-z0-9-]", "-", slug.lower()).strip("-")
    return f"admin-{value}"[:45].rstrip("-")


def create_user(db, email: str, username: str, full_name: str, role: SystemRole) -> tuple[User, str | None]:
    existing = db.execute(text("SELECT id FROM users WHERE lower(email)=:email"), {"email": email}).scalar_one_or_none()
    if existing is not None:
        user = db.get(User, existing)
        if role == SystemRole.SUPER_ADMIN:
            user.system_role = role
        return user, None

    initial_password = password()
    user = User(
        email=email,
        username=username,
        password_hash=hash_password(initial_password),
        status=AccountStatus.ACTIVE,
        system_role=role,
        email_verified_at=datetime.now(UTC),
    )
    user.profile = Profile(full_name=full_name)
    db.add(user)
    db.flush()
    return user, initial_password


def main() -> None:
    credentials = []
    with SessionLocal.begin() as db:
        super_admin, initial_password = create_user(
            db,
            "super-admin@hvnh.edu.vn",
            "super_admin",
            "Quản trị viên tổng HVNH Hub",
            SystemRole.SUPER_ADMIN,
        )
        credentials.append({"scope": "SUPER_ADMIN", "email": super_admin.email, "password": initial_password or "UNCHANGED"})

        groups = db.execute(
            text(
                "SELECT id, name, slug FROM groups "
                "WHERE status='ACTIVE' AND slug = ANY(:slugs) ORDER BY slug"
            ),
            {"slugs": list(CANONICAL_GROUP_SLUGS)},
        ).mappings()
        for group in groups:
            local = local_name(group["slug"])
            admin, initial_password = create_user(
                db,
                f"{local}@hvnh.edu.vn",
                local.replace("-", "_"),
                f"Quản trị nhóm {group['name']}",
                SystemRole.USER,
            )
            db.execute(
                text(
                    "INSERT INTO group_members (group_id,user_id,role) VALUES (:group_id,:user_id,'ADMIN') "
                    "ON CONFLICT (group_id,user_id) DO UPDATE SET role='ADMIN'"
                ),
                {"group_id": group["id"], "user_id": admin.id},
            )
            credentials.append({"scope": group["slug"], "email": admin.email, "password": initial_password or "UNCHANGED"})

    print(json.dumps(credentials, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
