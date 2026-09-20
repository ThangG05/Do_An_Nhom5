import json,uuid
from datetime import UTC,datetime
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.db.models.media import MediaFile,MediaStatus
from src.db.models.user import AccountStatus,SystemRole,User
from src.models.report import ReportCreateRequest,ReportResolveRequest,ReportResponse
from src.services.storage_service import create_download_url

def _target(db:Session,kind:str,target_id:uuid.UUID):
    if kind=="POST": return db.execute(text("SELECT p.group_id,p.author_id owner_id,left(p.content,240) summary FROM posts p WHERE p.id=:id AND p.deleted_at IS NULL"),{"id":target_id}).mappings().first()
    if kind=="COMMENT": return db.execute(text("SELECT p.group_id,c.user_id owner_id,left(c.content,240) summary FROM comments c JOIN posts p ON p.id=c.post_id WHERE c.id=:id AND c.deleted_at IS NULL AND p.deleted_at IS NULL"),{"id":target_id}).mappings().first()
    return db.execute(text("SELECT NULL::uuid group_id,u.id owner_id,COALESCE(p.full_name,u.username) summary FROM users u LEFT JOIN profiles p ON p.user_id=u.id WHERE u.id=:id AND u.deleted_at IS NULL"),{"id":target_id}).mappings().first()

def create(db:Session,user:User,payload:ReportCreateRequest)->uuid.UUID:
    target=_target(db,payload.target_type,payload.target_id)
    if not target: raise HTTPException(404,"Không tìm thấy đối tượng cần báo cáo.")
    if target["owner_id"]==user.id: raise HTTPException(400,"Bạn không thể báo cáo nội dung hoặc tài khoản của chính mình.")
    if payload.evidence_media_id:
        media=db.get(MediaFile,payload.evidence_media_id)
        if not media or media.owner_id!=user.id or media.status!=MediaStatus.READY: raise HTTPException(400,"Minh chứng không hợp lệ.")
    report_id=uuid.uuid4()
    try:
        db.execute(text("INSERT INTO reports(id,reporter_id,target_type,target_id,reason,evidence_media_id) VALUES(:id,:uid,CAST(:kind AS report_target_type),:target,:reason,:media)"),{"id":report_id,"uid":user.id,"kind":payload.target_type,"target":payload.target_id,"reason":payload.reason.strip(),"media":payload.evidence_media_id});db.commit()
    except IntegrityError as exc: db.rollback();raise HTTPException(409,"Bạn đã có báo cáo đang chờ xử lý cho đối tượng này.") from exc
    return report_id

def _group_ids(db:Session,user:User)->list[uuid.UUID]:
    return list(db.scalars(text("SELECT group_id FROM group_members WHERE user_id=:uid AND role='ADMIN'"),{"uid":user.id}))

def list_queue(db:Session,user:User,status:str|None=None)->list[ReportResponse]:
    params={"status":status};scope=""
    if user.system_role!=SystemRole.SUPER_ADMIN:
        ids=_group_ids(db,user)
        if not ids: raise HTTPException(403,"Bạn không có quyền xử lý báo cáo.")
        scope=" AND COALESCE(p.group_id,cp.group_id)=ANY(:groups)";params["groups"]=ids
    status_sql=" AND r.status::text=:status" if status else ""
    rows=db.execute(text("SELECT r.*,COALESCE(rp.full_name,ru.username,'Người dùng đã xóa') reporter_name,COALESCE(p.group_id,cp.group_id) group_id,g.name group_name,CASE WHEN r.target_type='POST' THEN left(p.content,240) WHEN r.target_type='COMMENT' THEN left(c.content,240) ELSE COALESCE(tp.full_name,tu.username,'Tài khoản đã xóa') END target_summary FROM reports r LEFT JOIN users ru ON ru.id=r.reporter_id LEFT JOIN profiles rp ON rp.user_id=ru.id LEFT JOIN posts p ON r.target_type='POST' AND p.id=r.target_id LEFT JOIN comments c ON r.target_type='COMMENT' AND c.id=r.target_id LEFT JOIN posts cp ON cp.id=c.post_id LEFT JOIN users tu ON r.target_type='USER' AND tu.id=r.target_id LEFT JOIN profiles tp ON tp.user_id=tu.id LEFT JOIN groups g ON g.id=COALESCE(p.group_id,cp.group_id) WHERE 1=1"+status_sql+scope+" ORDER BY r.created_at DESC"),params).mappings()
    out=[]
    for r in rows:
        evidence=None
        if r["evidence_media_id"]:
            media=db.get(MediaFile,r["evidence_media_id"]);evidence=create_download_url(media) if media and media.status==MediaStatus.READY else None
        out.append(ReportResponse(id=str(r["id"]),reporter_id=str(r["reporter_id"]) if r["reporter_id"] else None,reporter_name=r["reporter_name"],target_type=str(r["target_type"]),target_id=str(r["target_id"]),reason=r["reason"],status=str(r["status"]),group_id=str(r["group_id"]) if r["group_id"] else None,group_name=r["group_name"],target_summary=r["target_summary"] or "",evidence_url=evidence,resolution_note=r["resolution_note"],created_at=r["created_at"].isoformat(),handled_at=r["handled_at"].isoformat() if r["handled_at"] else None))
    return out

def resolve(db:Session,user:User,report_id:uuid.UUID,payload:ReportResolveRequest)->None:
    report=db.execute(text("SELECT * FROM reports WHERE id=:id AND status IN ('PENDING','REVIEWING') FOR UPDATE"),{"id":report_id}).mappings().first()
    if not report: raise HTTPException(404,"Không tìm thấy báo cáo đang chờ xử lý.")
    target=_target(db,str(report["target_type"]),report["target_id"])
    if user.system_role!=SystemRole.SUPER_ADMIN:
        if not target or not target["group_id"] or target["group_id"] not in _group_ids(db,user): raise HTTPException(403,"Báo cáo không thuộc nhóm bạn quản lý.")
        if payload.action in {"LOCK_USER","DISABLE_USER"}: raise HTTPException(403,"Group Admin không được xử lý tài khoản toàn hệ thống.")
    if payload.action=="HIDE_CONTENT":
        if str(report["target_type"])=="POST": db.execute(text("UPDATE posts SET status='DELETED',deleted_at=now() WHERE id=:id"),{"id":report["target_id"]})
        elif str(report["target_type"])=="COMMENT": db.execute(text("UPDATE comments SET deleted_at=now() WHERE id=:id"),{"id":report["target_id"]})
        else: raise HTTPException(400,"Không thể ẩn một tài khoản bằng hành động này.")
    if payload.action in {"LOCK_USER","DISABLE_USER"}:
        if str(report["target_type"])!="USER": raise HTTPException(400,"Hành động tài khoản chỉ áp dụng cho báo cáo USER.")
        target_user=db.get(User,report["target_id"])
        if not target_user or target_user.system_role==SystemRole.SUPER_ADMIN: raise HTTPException(403,"Không thể xử lý Super Admin.")
        target_user.status=AccountStatus.LOCKED if payload.action=="LOCK_USER" else AccountStatus.DISABLED
        db.execute(text("UPDATE refresh_tokens SET revoked_at=now() WHERE user_id=:uid AND revoked_at IS NULL"),{"uid":target_user.id})
    final="RESOLVED" if payload.decision=="RESOLVE" else "REJECTED"
    db.execute(text("UPDATE reports SET status=:status,handled_by=:admin,resolution_note=:note,handled_at=now() WHERE id=:id"),{"status":final,"admin":user.id,"note":payload.note.strip(),"id":report_id})
    db.execute(text("INSERT INTO audit_logs(actor_id,action,target_type,target_id,metadata) VALUES(:actor,'REPORT_HANDLED','REPORT',:id,CAST(:meta AS jsonb))"),{"actor":user.id,"id":report_id,"meta":json.dumps({"decision":payload.decision,"action":payload.action},ensure_ascii=False)})
    if report["reporter_id"]: db.execute(text("INSERT INTO notifications(user_id,type,title,content,actor_id,reference_type,reference_id) VALUES(:uid,'SYSTEM','Kết quả báo cáo',:content,:actor,'REPORT',:id)"),{"uid":report["reporter_id"],"content":payload.note.strip(),"actor":user.id,"id":report_id})
    db.commit()
