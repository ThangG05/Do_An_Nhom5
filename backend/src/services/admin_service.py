import uuid
from io import BytesIO
from datetime import UTC, datetime

from fastapi import HTTPException
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db.models.user import AccountStatus, SystemRole, User
from src.models.admin import AdminDashboardResponse, AdminUserPage, AdminUserResponse, AuditLogResponse, DisciplineRequest


def _count(db: Session, sql: str, params: dict | None = None) -> int:
    return int(db.execute(text(sql), params or {}).scalar() or 0)


def dashboard(db: Session) -> AdminDashboardResponse:
    group_rows = db.execute(text("SELECT g.id,g.name,g.slug,count(DISTINCT gm.user_id) members,count(DISTINCT p.id) FILTER(WHERE p.status='APPROVED' AND p.deleted_at IS NULL) approved_posts,count(DISTINCT p.id) FILTER(WHERE p.status='PENDING' AND p.deleted_at IS NULL) pending_posts FROM groups g LEFT JOIN group_members gm ON gm.group_id=g.id LEFT JOIN posts p ON p.group_id=g.id WHERE g.status='ACTIVE' GROUP BY g.id ORDER BY g.name")).mappings()
    activity_rows = db.execute(text("""
        SELECT day::date AS date,
          (SELECT count(*) FROM users u WHERE u.created_at >= day AND u.created_at < day + interval '1 day' AND u.deleted_at IS NULL) AS new_users,
          (SELECT count(*) FROM posts p WHERE p.created_at >= day AND p.created_at < day + interval '1 day' AND p.deleted_at IS NULL) AS posts,
          (SELECT count(*) FROM messages m WHERE m.created_at >= day AND m.created_at < day + interval '1 day' AND m.deleted_at IS NULL) AS messages
        FROM generate_series(current_date - interval '13 days', current_date, interval '1 day') day
        ORDER BY day
    """)).mappings()
    return AdminDashboardResponse(
        total_users=_count(db,"SELECT count(*) FROM users WHERE deleted_at IS NULL"),
        active_users=_count(db,"SELECT count(*) FROM users WHERE status='ACTIVE' AND deleted_at IS NULL"),
        locked_users=_count(db,"SELECT count(*) FROM users WHERE status='LOCKED' AND deleted_at IS NULL"),
        disabled_users=_count(db,"SELECT count(*) FROM users WHERE status='DISABLED' AND deleted_at IS NULL"),
        pending_posts=_count(db,"SELECT count(*) FROM posts WHERE status='PENDING' AND deleted_at IS NULL"),
        approved_posts=_count(db,"SELECT count(*) FROM posts WHERE status='APPROVED' AND deleted_at IS NULL"),
        rejected_posts=_count(db,"SELECT count(*) FROM posts WHERE status='REJECTED' AND deleted_at IS NULL"),
        total_likes=_count(db,"SELECT count(*) FROM post_likes"), total_comments=_count(db,"SELECT count(*) FROM comments WHERE deleted_at IS NULL"), total_messages=_count(db,"SELECT count(*) FROM messages WHERE deleted_at IS NULL"), groups=[dict(row) for row in group_rows], activity=[{"date":row["date"].isoformat(),"new_users":row["new_users"],"posts":row["posts"],"messages":row["messages"]} for row in activity_rows],
    )


def export_workbook(db: Session) -> BytesIO:
    stats = dashboard(db)
    workbook = Workbook()
    overview = workbook.active
    overview.title = "Tổng quan"
    overview.append(["BÁO CÁO VẬN HÀNH HVNH HUB", datetime.now(UTC).strftime("%d/%m/%Y %H:%M UTC")])
    overview.append([])
    overview.append(["Chỉ số", "Giá trị"])
    metrics = [
        ("Tổng người dùng", stats.total_users), ("Người dùng hoạt động", stats.active_users),
        ("Tài khoản bị khóa", stats.locked_users), ("Tài khoản vô hiệu hóa", stats.disabled_users),
        ("Bài chờ duyệt", stats.pending_posts), ("Bài đã duyệt", stats.approved_posts),
        ("Bài bị từ chối", stats.rejected_posts), ("Lượt thích", stats.total_likes),
        ("Bình luận", stats.total_comments), ("Tin nhắn", stats.total_messages),
    ]
    for row in metrics: overview.append(row)

    groups_sheet = workbook.create_sheet("Nhóm")
    groups_sheet.append(["Tên nhóm", "Slug", "Thành viên", "Bài đã duyệt", "Bài chờ duyệt"])
    for group in stats.groups:
        groups_sheet.append([group["name"], group["slug"], group["members"], group["approved_posts"], group["pending_posts"]])

    activity_sheet = workbook.create_sheet("Hoạt động 14 ngày")
    activity_sheet.append(["Ngày", "Người dùng mới", "Bài viết", "Tin nhắn"])
    for item in stats.activity:
        activity_sheet.append([item["date"], item["new_users"], item["posts"], item["messages"]])

    users_sheet = workbook.create_sheet("Người dùng")
    users_sheet.append(["Email", "Username", "Họ tên", "Mã sinh viên", "Khoa", "Trạng thái", "Vai trò", "Ngày tạo", "Đăng nhập gần nhất"])
    rows = db.execute(text("""
        SELECT u.email,u.username,COALESCE(p.full_name,u.username) full_name,p.student_code,p.faculty,
               u.status::text status,u.system_role::text system_role,u.created_at,u.last_login_at
        FROM users u LEFT JOIN profiles p ON p.user_id=u.id
        WHERE u.deleted_at IS NULL ORDER BY u.created_at DESC
    """)).mappings()
    for row in rows:
        users_sheet.append([row["email"],row["username"],row["full_name"],row["student_code"],row["faculty"],row["status"],row["system_role"],row["created_at"].replace(tzinfo=None),row["last_login_at"].replace(tzinfo=None) if row["last_login_at"] else None])

    reports_sheet=workbook.create_sheet("Báo cáo vi phạm")
    reports_sheet.append(["Loại","Đối tượng","Lý do","Trạng thái","Ngày tạo","Ngày xử lý"])
    report_rows=db.execute(text("SELECT target_type::text,target_id,reason,status::text,created_at,handled_at FROM reports ORDER BY created_at DESC")).mappings()
    for row in report_rows:reports_sheet.append([row["target_type"],str(row["target_id"]),row["reason"],row["status"],row["created_at"].replace(tzinfo=None),row["handled_at"].replace(tzinfo=None) if row["handled_at"] else None])

    navy = PatternFill("solid", fgColor="002855")
    for sheet in workbook.worksheets:
        header_row = 3 if sheet is overview else 1
        for cell in sheet[header_row]:
            cell.fill = navy
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")
        sheet.freeze_panes = f"A{header_row + 1}"
        sheet.auto_filter.ref = sheet.dimensions if sheet.max_row >= header_row else None
        for column in sheet.columns:
            letter = column[0].column_letter
            sheet.column_dimensions[letter].width = min(42, max(12, max(len(str(cell.value or "")) for cell in column) + 2))
    overview["A1"].font = Font(size=16, bold=True, color="002855")
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def _serialize_user(db: Session, row) -> AdminUserResponse:
    groups=[dict(item) for item in db.execute(text("SELECT g.id::text id,g.name,g.slug FROM group_members gm JOIN groups g ON g.id=gm.group_id WHERE gm.user_id=:uid AND gm.role='ADMIN' ORDER BY g.name"),{"uid":row["id"]}).mappings()]
    return AdminUserResponse(id=str(row["id"]),email=row["email"],username=row["username"],full_name=row["full_name"],student_code=row["student_code"],faculty=row["faculty"],status=str(row["status"]),system_role=str(row["system_role"]),admin_groups=groups,created_at=row["created_at"].isoformat(),last_login_at=row["last_login_at"].isoformat() if row["last_login_at"] else None,suspended_until=row["suspended_until"].isoformat() if row["suspended_until"] else None,warning_count=row["warning_count"] or 0)


def users(db: Session, q: str, account_status: str | None, limit: int, offset: int) -> AdminUserPage:
    where=["u.deleted_at IS NULL"];params={"pattern":f"%{q.strip()}%","limit":limit,"offset":offset}
    if q.strip(): where.append("(u.email ILIKE :pattern OR u.username ILIKE :pattern OR p.full_name ILIKE :pattern OR p.student_code ILIKE :pattern OR p.faculty ILIKE :pattern)")
    if account_status: where.append("u.status::text=:status");params["status"]=account_status
    clause=" AND ".join(where)
    total=_count(db,f"SELECT count(*) FROM users u LEFT JOIN profiles p ON p.user_id=u.id WHERE {clause}",params)
    rows=db.execute(text(f"SELECT u.id,u.email,u.username,u.status,u.system_role,u.created_at,u.last_login_at,u.suspended_until,u.warning_count,COALESCE(p.full_name,u.username) full_name,p.student_code,p.faculty FROM users u LEFT JOIN profiles p ON p.user_id=u.id WHERE {clause} ORDER BY u.created_at DESC LIMIT :limit OFFSET :offset"),params).mappings()
    return AdminUserPage(items=[_serialize_user(db,row) for row in rows],total=total,limit=limit,offset=offset)


def _target(db: Session, user_id: uuid.UUID, actor: User) -> User:
    target=db.get(User,user_id)
    if not target or target.deleted_at is not None: raise HTTPException(404,"Không tìm thấy tài khoản.")
    if target.id==actor.id or target.system_role==SystemRole.SUPER_ADMIN: raise HTTPException(403,"Không thể thay đổi tài khoản Super Admin.")
    return target


def _audit(db: Session, actor: User, action: str, target: uuid.UUID, metadata: dict) -> None:
    db.execute(text("INSERT INTO audit_logs(actor_id,action,target_type,target_id,metadata) VALUES(:actor,:action,'USER',:target,CAST(:metadata AS jsonb))"),{"actor":actor.id,"action":action,"target":target,"metadata":__import__('json').dumps(metadata,ensure_ascii=False)})


def set_status(db: Session, user_id: uuid.UUID, actor: User, value: str, reason: str) -> None:
    target=_target(db,user_id,actor);old=target.status.value;target.status=AccountStatus(value)
    if target.status!=AccountStatus.ACTIVE: db.execute(text("UPDATE refresh_tokens SET revoked_at=now() WHERE user_id=:uid AND revoked_at IS NULL"),{"uid":target.id})
    _audit(db,actor,"ACCOUNT_STATUS_CHANGED",target.id,{"from":old,"to":value,"reason":reason})
    db.execute(text("INSERT INTO notifications(user_id,type,title,content,actor_id,reference_type,reference_id) VALUES(:uid,'SYSTEM','Trạng thái tài khoản thay đổi',:content,:actor,'USER',:uid)"),{"uid":target.id,"content":f"Tài khoản chuyển sang {value}. Lý do: {reason}","actor":actor.id})
    db.commit()


def set_group_admin(db: Session, user_id: uuid.UUID, group_id: uuid.UUID, actor: User, grant: bool) -> None:
    target=_target(db,user_id,actor)
    group=db.execute(text("SELECT name FROM groups WHERE id=:id AND status='ACTIVE'"),{"id":group_id}).scalar_one_or_none()
    if not group: raise HTTPException(404,"Không tìm thấy nhóm.")
    if grant: db.execute(text("INSERT INTO group_members(group_id,user_id,role) VALUES(:gid,:uid,'ADMIN') ON CONFLICT(group_id,user_id) DO UPDATE SET role='ADMIN'"),{"gid":group_id,"uid":target.id})
    else: db.execute(text("DELETE FROM group_members WHERE group_id=:gid AND user_id=:uid AND role='ADMIN'"),{"gid":group_id,"uid":target.id})
    _audit(db,actor,"GROUP_ADMIN_GRANTED" if grant else "GROUP_ADMIN_REVOKED",target.id,{"group_id":str(group_id),"group_name":group})
    db.commit()


def discipline(db:Session,user_id:uuid.UUID,actor:User,payload:DisciplineRequest)->None:
    from datetime import timedelta
    target=_target(db,user_id,actor);now=datetime.now(UTC)
    if payload.action=="WARN":
        target.warning_count+=1
    elif payload.action=="SUSPEND":
        if not payload.duration_days:raise HTTPException(400,"Phải chọn thời hạn tạm khóa.")
        target.status=AccountStatus.LOCKED;target.suspended_until=now+timedelta(days=payload.duration_days)
    elif payload.action=="BAN":
        target.status=AccountStatus.DISABLED;target.suspended_until=None
    else:
        target.status=AccountStatus.ACTIVE;target.suspended_until=None;target.failed_login_attempts=0;target.login_locked_until=None
    if payload.action in {"SUSPEND","BAN"}:db.execute(text("UPDATE refresh_tokens SET revoked_at=now() WHERE user_id=:uid AND revoked_at IS NULL"),{"uid":target.id})
    _audit(db,actor,f"USER_{payload.action}",target.id,{"reason":payload.reason,"duration_days":payload.duration_days})
    db.execute(text("INSERT INTO notifications(user_id,type,title,content,actor_id,reference_type,reference_id) VALUES(:uid,'SYSTEM','Xử lý tài khoản',:content,:actor,'USER',:uid)"),{"uid":target.id,"content":f"{payload.action}: {payload.reason}","actor":actor.id})
    db.commit()


def audit_logs(db:Session,limit:int=100)->list[AuditLogResponse]:
    rows=db.execute(text("SELECT a.id,a.action,a.target_type,a.target_id,a.metadata,a.created_at,COALESCE(p.full_name,u.username,'Hệ thống') actor_name FROM audit_logs a LEFT JOIN users u ON u.id=a.actor_id LEFT JOIN profiles p ON p.user_id=u.id ORDER BY a.created_at DESC LIMIT :limit"),{"limit":limit}).mappings()
    return [AuditLogResponse(id=str(r["id"]),actor_name=r["actor_name"],action=r["action"],target_type=r["target_type"],target_id=str(r["target_id"]) if r["target_id"] else None,metadata=r["metadata"] or {},created_at=r["created_at"].isoformat()) for r in rows]
