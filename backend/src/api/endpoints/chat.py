import json,uuid
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException,WebSocket,WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.api.dependencies import CurrentUser
from src.db.models.chat import ConversationMember
from src.db.models.user import AccountStatus,User
from src.db.session import SessionLocal,get_db
from src.models.chat import ConversationResponse,ConversationSettingsRequest,DirectConversationRequest,MessageResponse,SendMessageRequest,SharedAttachmentsResponse,UnreadMessagesResponse
from src.services import chat_service
from src.services.realtime_service import manager

router=APIRouter(prefix="/chat",tags=["Chat"])

@router.get("/conversations",response_model=list[ConversationResponse])
async def conversations(current_user:CurrentUser,db:Annotated[Session,Depends(get_db)]):
    rows=chat_service.list_conversations(db,current_user)
    for row in rows:
        if row.participantId:
            row.isOnline=await manager.is_online(uuid.UUID(row.participantId))
            row.lastActive="Đang hoạt động" if row.isOnline else "Ngoại tuyến"
    return rows

@router.post("/conversations/direct",response_model=ConversationResponse)
def direct(payload:DirectConversationRequest,current_user:CurrentUser,db:Annotated[Session,Depends(get_db)]):
    target=db.get(User,payload.target_user_id)
    if not target or target.deleted_at is not None:raise HTTPException(404,"Không tìm thấy người dùng.")
    conv=chat_service.get_or_create_direct(db,current_user,target)
    return next(x for x in chat_service.list_conversations(db,current_user) if x.id==str(conv.id))

@router.get("/conversations/{conversation_id}/messages",response_model=list[MessageResponse])
async def messages(conversation_id:uuid.UUID,current_user:CurrentUser,db:Annotated[Session,Depends(get_db)],limit:int=50,before:datetime|None=None):
    result=chat_service.list_messages(db,conversation_id,current_user,min(max(limit,1),100),before)
    peers=list(db.scalars(select(ConversationMember.user_id).where(ConversationMember.conversation_id==conversation_id,ConversationMember.user_id!=current_user.id,ConversationMember.left_at.is_(None))).all())
    await manager.send_users(peers,{"event":"messages.seen","conversation_id":str(conversation_id),"seen_by":str(current_user.id)})
    return result

@router.get("/conversations/{conversation_id}/messages/search",response_model=list[MessageResponse])
def search_messages(conversation_id:uuid.UUID,q:str,current_user:CurrentUser,db:Annotated[Session,Depends(get_db)],limit:int=50):
    return chat_service.search_messages(db,conversation_id,current_user,q,min(max(limit,1),100))

@router.get("/conversations/{conversation_id}/shared",response_model=SharedAttachmentsResponse)
def shared_attachments(conversation_id:uuid.UUID,current_user:CurrentUser,db:Annotated[Session,Depends(get_db)],limit:int=100):
    return chat_service.shared_attachments(db,conversation_id,current_user,min(max(limit,1),200))

@router.patch("/conversations/{conversation_id}/settings",status_code=204)
async def conversation_settings(conversation_id:uuid.UUID,payload:ConversationSettingsRequest,current_user:CurrentUser,db:Annotated[Session,Depends(get_db)]):
    chat_service.update_settings(db,conversation_id,current_user,payload)
    recipients=list(db.scalars(select(ConversationMember.user_id).where(ConversationMember.conversation_id==conversation_id,ConversationMember.left_at.is_(None))).all())
    await manager.send_users(recipients,{"event":"conversation.updated","conversation_id":str(conversation_id)})

@router.post("/conversations/{conversation_id}/messages",response_model=MessageResponse,status_code=201)
async def send_message(conversation_id:uuid.UUID,payload:SendMessageRequest,current_user:CurrentUser,db:Annotated[Session,Depends(get_db)]):
    message=chat_service.send(db,conversation_id,current_user,payload)
    recipients=list(db.scalars(select(ConversationMember.user_id).where(ConversationMember.conversation_id==conversation_id,ConversationMember.left_at.is_(None))).all())
    await manager.send_users(recipients,{"event":"message.created","conversation_id":str(conversation_id),"message":message.model_dump(mode="json")})
    await manager.send_users([uid for uid in recipients if uid!=current_user.id],{"event":"notification.created","type":"MESSAGE"})
    return message

@router.get("/unread-count",response_model=UnreadMessagesResponse)
def unread(current_user:CurrentUser,db:Annotated[Session,Depends(get_db)]):return UnreadMessagesResponse(unread_count=chat_service.unread_count(db,current_user.id))

@router.post("/ws-ticket")
async def websocket_ticket(current_user:CurrentUser):
    """Issue a short-lived, single-use credential so bearer tokens never enter URLs."""
    from src.config import settings
    return {"ticket":await manager.issue_ticket(current_user.id),"expires_in":settings.WEBSOCKET_TICKET_EXPIRE_SECONDS}

@router.websocket("/ws")
async def websocket_chat(websocket:WebSocket,ticket:str):
    db=SessionLocal()
    connected=False;uid=None;peers=[]
    try:
        try:uid=await manager.consume_ticket(ticket)
        except Exception:uid=None
        if uid is None:await websocket.close(code=4401);return
        user=db.get(User,uid)
        if not user or user.status!=AccountStatus.ACTIVE:await websocket.close(code=4403);return
        await manager.connect(uid,websocket)
        connected=True
        peers=list(db.scalars(select(ConversationMember.user_id).where(ConversationMember.user_id!=uid,ConversationMember.left_at.is_(None),ConversationMember.conversation_id.in_(select(ConversationMember.conversation_id).where(ConversationMember.user_id==uid,ConversationMember.left_at.is_(None))))).all())
        await manager.send_users(peers,{"event":"presence.changed","user_id":str(uid),"online":True})
        try:
            while True:
                raw=await websocket.receive_text()
                if raw=="ping":continue
                if len(raw)>65536:continue
                try:data=json.loads(raw)
                except json.JSONDecodeError:continue
                event=data.get("event")
                if event not in {"call.offer","call.answer","call.ice","call.end"}:continue
                try:cid=uuid.UUID(str(data.get("conversation_id","")))
                except ValueError:continue
                membership=db.get(ConversationMember,(cid,uid))
                if not membership or membership.left_at is not None:continue
                recipients=list(db.scalars(select(ConversationMember.user_id).where(ConversationMember.conversation_id==cid,ConversationMember.user_id!=uid,ConversationMember.left_at.is_(None))).all())
                outgoing={"event":event,"conversation_id":str(cid),"from_user_id":str(uid)}
                if event in {"call.offer","call.answer"} and isinstance(data.get("sdp"),dict):outgoing["sdp"]=data["sdp"]
                if event=="call.offer":outgoing["video"]=bool(data.get("video"))
                if event=="call.ice" and isinstance(data.get("candidate"),dict):outgoing["candidate"]=data["candidate"]
                if event=="call.end":outgoing["reason"]=str(data.get("reason","ended"))[:30]
                await manager.send_users(recipients,outgoing)
        except WebSocketDisconnect:
            pass
    finally:
        if connected and uid is not None:
            await manager.disconnect(uid,websocket)
            if not await manager.is_online(uid):await manager.send_users(peers,{"event":"presence.changed","user_id":str(uid),"online":False})
        db.close()
