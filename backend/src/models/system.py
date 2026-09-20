import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel,Field
class MaintenanceResponse(BaseModel):enabled:bool=False;message:str="";expected_end_at:datetime|None=None
class MaintenanceUpdate(MaintenanceResponse):message:str=Field(min_length=3,max_length=1000)
class KeywordCreate(BaseModel):keyword:str=Field(min_length=2,max_length=255);action:Literal['BLOCK','REVIEW']='BLOCK'
class KeywordUpdate(BaseModel):keyword:str|None=Field(default=None,min_length=2,max_length=255);action:Literal['BLOCK','REVIEW']|None=None;is_active:bool|None=None
class KeywordResponse(BaseModel):id:uuid.UUID;keyword:str;action:str;is_active:bool;created_at:datetime
