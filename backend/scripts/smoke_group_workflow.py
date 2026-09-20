"""Run and clean up a Neon smoke test for the complete group moderation workflow."""
from sqlalchemy import select, text

from src.db.models.user import User
from src.db.session import SessionLocal
from src.models.group import GroupPostCreateRequest, ModerationRequest
from src.services import group_service


def main() -> None:
    db = SessionLocal()
    request_id = post_id = group_id = user_id = None
    try:
        group_id = db.execute(text("SELECT id FROM groups WHERE slug='pass-do'")).scalar_one()
        user = db.scalar(select(User).where(User.email == "student2@hvnh.edu.vn"))
        admin = db.scalar(select(User).where(User.email == "admin-pass-do@hvnh.edu.vn"))
        if not user or not admin:
            raise RuntimeError("Thiếu tài khoản smoke test.")
        user_id = user.id
        if group_service._membership(db, group_id, user.id) != "NONE":
            raise RuntimeError("student2 đã có dữ liệu nhóm; dừng để không ảnh hưởng dữ liệu thật.")

        group_service.request_join(db, group_id, user)
        request_id = db.execute(text("SELECT id FROM group_join_requests WHERE group_id=:gid AND user_id=:uid"), {"gid": group_id, "uid": user.id}).scalar_one()
        group_service.decide_join(db, group_id, request_id, admin, True)
        post = group_service.create_post(db, group_id, user, GroupPostCreateRequest(content="SMOKE_GROUP_WORKFLOW", media_ids=[]))
        post_id = post.id
        approved = group_service.moderate_post(db, group_id, post_id, admin, ModerationRequest(decision="APPROVE"))
        group_service.pin_post(db, group_id, post_id, True)
        assert approved.status == "APPROVED"
        print("GROUP_WORKFLOW_OK")
    finally:
        if post_id:
            db.execute(text("DELETE FROM notifications WHERE reference_id=:pid"), {"pid": post_id})
            db.execute(text("DELETE FROM posts WHERE id=:pid"), {"pid": post_id})
        if group_id and user_id:
            db.execute(text("DELETE FROM group_members WHERE group_id=:gid AND user_id=:uid"), {"gid": group_id, "uid": user_id})
            db.execute(text("DELETE FROM group_join_requests WHERE group_id=:gid AND user_id=:uid"), {"gid": group_id, "uid": user_id})
        db.commit()
        db.close()


if __name__ == "__main__":
    main()
