import json,re,unicodedata,uuid
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.db.models.user import User
from src.models.system import KeywordCreate,KeywordResponse,KeywordUpdate,MaintenanceResponse,MaintenanceUpdate

def maintenance(db:Session)->MaintenanceResponse:
 value=db.execute(text("SELECT value FROM system_settings WHERE key='maintenance'")).scalar() or {};return MaintenanceResponse(**value)
def set_maintenance(db:Session,user:User,payload:MaintenanceUpdate)->MaintenanceResponse:
 value=payload.model_dump(mode='json');db.execute(text("INSERT INTO system_settings(key,value,updated_by,updated_at) VALUES('maintenance',CAST(:value AS jsonb),:uid,now()) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value,updated_by=EXCLUDED.updated_by,updated_at=now()"),{"value":json.dumps(value,ensure_ascii=False),"uid":user.id});audit(db,user,"MAINTENANCE_UPDATED",None,value);db.commit();return payload
def keywords(db:Session)->list[KeywordResponse]:return [KeywordResponse(**r) for r in db.execute(text("SELECT id,keyword,action,is_active,created_at FROM blacklist_keywords ORDER BY created_at DESC")).mappings()]
def add_keyword(db:Session,user:User,payload:KeywordCreate)->KeywordResponse:
 keyword=payload.keyword.strip().lower()
 try:
  row=db.execute(text("INSERT INTO blacklist_keywords(keyword,action,created_by) VALUES(:keyword,:action,:uid) RETURNING id,keyword,action,is_active,created_at"),{"keyword":keyword,"action":payload.action,"uid":user.id}).mappings().one();audit(db,user,"BLACKLIST_CREATED",row['id'],{"keyword":keyword,"action":payload.action});db.commit();return KeywordResponse(**row)
 except IntegrityError as exc:db.rollback();raise HTTPException(409,"Từ khóa đã tồn tại.") from exc
def update_keyword(db:Session,user:User,item_id:uuid.UUID,payload:KeywordUpdate)->KeywordResponse:
 values=payload.model_dump(exclude_unset=True);values={k:(v.strip().lower() if k=='keyword' else v) for k,v in values.items()};sets=','.join(f"{k}=:{k}" for k in values)
 if not sets:raise HTTPException(400,"Không có thay đổi.")
 row=db.execute(text(f"UPDATE blacklist_keywords SET {sets},updated_at=now() WHERE id=:id RETURNING id,keyword,action,is_active,created_at"),{**values,"id":item_id}).mappings().first()
 if not row:raise HTTPException(404,"Không tìm thấy từ khóa.")
 audit(db,user,"BLACKLIST_UPDATED",item_id,values);db.commit();return KeywordResponse(**row)
def delete_keyword(db:Session,user:User,item_id:uuid.UUID):
 row=db.execute(text("DELETE FROM blacklist_keywords WHERE id=:id RETURNING keyword"),{"id":item_id}).first()
 if not row:raise HTTPException(404,"Không tìm thấy từ khóa.")
 audit(db,user,"BLACKLIST_DELETED",item_id,{"keyword":row.keyword});db.commit()
def audit(db,user,action,target,meta):db.execute(text("INSERT INTO audit_logs(actor_id,action,target_type,target_id,metadata) VALUES(:uid,:action,'SYSTEM_CONFIG',:target,CAST(:meta AS jsonb))"),{"uid":user.id,"action":action,"target":target,"meta":json.dumps(meta,ensure_ascii=False)})
def check_content(db:Session,content:str)->str|None:
 normalized=unicodedata.normalize('NFKC',content).casefold()
 for keyword,action in db.execute(text("SELECT keyword,action FROM blacklist_keywords WHERE is_active=true ORDER BY length(keyword) DESC")):
  if keyword.casefold() in normalized:return str(action)
 return None
def enforce_content(db:Session,content:str,allow_review:bool=False)->str|None:
 action=check_content(db,content)
 if action=='BLOCK' or (action=='REVIEW' and not allow_review):raise HTTPException(400,"Nội dung chứa từ khóa không được phép.")
 return action
