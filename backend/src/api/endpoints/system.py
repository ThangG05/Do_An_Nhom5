import uuid
from typing import Annotated
from fastapi import APIRouter,Depends,Response
from sqlalchemy.orm import Session
from src.api.dependencies import CurrentSuperAdmin
from src.db.session import get_db
from src.models.system import KeywordCreate,KeywordResponse,KeywordUpdate,MaintenanceResponse,MaintenanceUpdate
from src.services import system_service
router=APIRouter(prefix="/system",tags=["System Configuration"]);Db=Annotated[Session,Depends(get_db)]
@router.get("/status",response_model=MaintenanceResponse)
def status(db:Db):return system_service.maintenance(db)
@router.put("/admin/maintenance",response_model=MaintenanceResponse)
def maintenance(payload:MaintenanceUpdate,admin:CurrentSuperAdmin,db:Db):return system_service.set_maintenance(db,admin,payload)
@router.get("/admin/keywords",response_model=list[KeywordResponse])
def keywords(admin:CurrentSuperAdmin,db:Db):return system_service.keywords(db)
@router.post("/admin/keywords",response_model=KeywordResponse,status_code=201)
def add(payload:KeywordCreate,admin:CurrentSuperAdmin,db:Db):return system_service.add_keyword(db,admin,payload)
@router.patch("/admin/keywords/{item_id}",response_model=KeywordResponse)
def update(item_id:uuid.UUID,payload:KeywordUpdate,admin:CurrentSuperAdmin,db:Db):return system_service.update_keyword(db,admin,item_id,payload)
@router.delete("/admin/keywords/{item_id}",status_code=204)
def delete(item_id:uuid.UUID,admin:CurrentSuperAdmin,db:Db):system_service.delete_keyword(db,admin,item_id);return Response(status_code=204)
