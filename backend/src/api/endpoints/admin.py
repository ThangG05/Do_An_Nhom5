import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from src.api.dependencies import CurrentSuperAdmin
from src.db.session import get_db
from src.models.admin import AdminDashboardResponse, AdminUserPage, AccountStatusRequest, GroupRoleRequest, DisciplineRequest, AuditLogResponse
from src.services import admin_service

router=APIRouter(prefix="/admin",tags=["Super Admin"]);Db=Annotated[Session,Depends(get_db)]

@router.get("/dashboard",response_model=AdminDashboardResponse)
def dashboard(admin:CurrentSuperAdmin,db:Db):return admin_service.dashboard(db)

@router.get("/dashboard/export")
def export_dashboard(admin:CurrentSuperAdmin,db:Db):
    filename=f"hvnh-hub-dashboard-{__import__('datetime').date.today().isoformat()}.xlsx"
    return StreamingResponse(admin_service.export_workbook(db),media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":f'attachment; filename="{filename}"'})

@router.get("/users",response_model=AdminUserPage)
def users(admin:CurrentSuperAdmin,db:Db,q:str="",account_status:Annotated[str|None,Query(alias="status")]=None,limit:Annotated[int,Query(ge=1,le=100)]=30,offset:Annotated[int,Query(ge=0)]=0):return admin_service.users(db,q,account_status,limit,offset)

@router.patch("/users/{user_id}/status",status_code=204)
def status(user_id:uuid.UUID,payload:AccountStatusRequest,admin:CurrentSuperAdmin,db:Db):admin_service.set_status(db,user_id,admin,payload.status,payload.reason);return Response(status_code=204)

@router.put("/users/{user_id}/group-admin",status_code=204)
def group_role(user_id:uuid.UUID,payload:GroupRoleRequest,admin:CurrentSuperAdmin,db:Db):admin_service.set_group_admin(db,user_id,payload.group_id,admin,payload.grant);return Response(status_code=204)

@router.post("/users/{user_id}/discipline",status_code=204)
def discipline(user_id:uuid.UUID,payload:DisciplineRequest,admin:CurrentSuperAdmin,db:Db):admin_service.discipline(db,user_id,admin,payload);return Response(status_code=204)

@router.get("/audit-logs",response_model=list[AuditLogResponse])
def audit_logs(admin:CurrentSuperAdmin,db:Db,limit:Annotated[int,Query(ge=1,le=500)]=100):return admin_service.audit_logs(db,limit)
