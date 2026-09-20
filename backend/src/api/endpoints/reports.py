import uuid
from typing import Annotated
from fastapi import APIRouter,Depends,Query,Response
from sqlalchemy.orm import Session
from src.api.dependencies import CurrentUser
from src.db.session import get_db
from src.models.report import ReportCreateRequest,ReportResolveRequest,ReportResponse
from src.services import report_service

router=APIRouter(prefix="/reports",tags=["Reports"]);Db=Annotated[Session,Depends(get_db)]

@router.post("",status_code=201)
def create(payload:ReportCreateRequest,user:CurrentUser,db:Db):return {"id":str(report_service.create(db,user,payload)),"message":"Đã gửi báo cáo."}

@router.get("/admin",response_model=list[ReportResponse])
def queue(user:CurrentUser,db:Db,report_status:Annotated[str|None,Query(alias="status")]=None):return report_service.list_queue(db,user,report_status)

@router.patch("/admin/{report_id}",status_code=204)
def resolve(report_id:uuid.UUID,payload:ReportResolveRequest,user:CurrentUser,db:Db):report_service.resolve(db,user,report_id,payload);return Response(status_code=204)
