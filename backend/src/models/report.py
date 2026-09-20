import uuid
from typing import Literal
from pydantic import BaseModel,Field

class ReportCreateRequest(BaseModel):
    target_type:Literal["USER","POST","COMMENT"]
    target_id:uuid.UUID
    reason:str=Field(min_length=5,max_length=3000)
    evidence_media_id:uuid.UUID|None=None

class ReportResolveRequest(BaseModel):
    decision:Literal["RESOLVE","REJECT"]
    action:Literal["NONE","HIDE_CONTENT","LOCK_USER","DISABLE_USER"]="NONE"
    note:str=Field(min_length=3,max_length=3000)

class ReportResponse(BaseModel):
    id:str;reporter_id:str|None;reporter_name:str;target_type:str;target_id:str;reason:str;status:str
    group_id:str|None=None;group_name:str|None=None;target_summary:str="";evidence_url:str|None=None
    resolution_note:str|None=None;created_at:str;handled_at:str|None=None
