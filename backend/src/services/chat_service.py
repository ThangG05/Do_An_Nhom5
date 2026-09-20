import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from src.db.models.chat import Conversation,ConversationMember,ConversationType,Message,MessageAttachment,MessageReceipt,MessageType
from src.db.models.media import MediaFile,MediaStatus
from src.db.models.user import User
from src.models.chat import AttachmentResponse,ConversationResponse,ConversationSettingsRequest,MessageResponse,SendMessageRequest,SharedAttachmentsResponse
from src.services.storage_service import create_download_url

def _avatar(db,user):
    if user and user.profile and user.profile.avatar_media_id:
        m=db.get(MediaFile,user.profile.avatar_media_id)
        if m and m.status==MediaStatus.READY:return create_download_url(m)
    return "/assets/logo.png"

def _member(db,cid,uid):
    member=db.get(ConversationMember,(cid,uid))
    if not member or member.left_at is not None: raise HTTPException(403,"Bạn không thuộc cuộc trò chuyện này.")
    return member

def _ensure_not_blocked(db:Session,cid:uuid.UUID,uid:uuid.UUID)->None:
    from src.services.block_service import is_blocked
    peers=db.scalars(select(ConversationMember.user_id).where(ConversationMember.conversation_id==cid,ConversationMember.user_id!=uid,ConversationMember.left_at.is_(None))).all()
    if any(is_blocked(db,uid,peer_id) for peer_id in peers):raise HTTPException(403,"Không thể truy cập cuộc trò chuyện do quan hệ chặn.")

def _file_size(value:int)->str:
    size=float(value)
    for unit in ("B","KB","MB","GB"):
        if size<1024 or unit=="GB":return f"{size:.0f} {unit}" if unit=="B" else f"{size:.1f} {unit}"
        size/=1024
    return f"{value} B"

def _attachment(media:MediaFile)->AttachmentResponse:
    kind="image" if media.mime_type.startswith("image/") else "video" if media.mime_type.startswith("video/") else "audio" if media.mime_type.startswith("audio/") else "file"
    return AttachmentResponse(id=str(media.id),type=kind,url=create_download_url(media),name=media.original_name or "media",size=_file_size(media.file_size))

def get_or_create_direct(db,actor:User,target:User):
    from src.services.block_service import is_blocked
    if is_blocked(db,actor.id,target.id):raise HTTPException(403,"Không thể nhắn tin do quan hệ chặn.")
    if actor.id==target.id: raise HTTPException(400,"Không thể tự nhắn tin cho chính mình.")
    low,high=sorted((actor.id,target.id))
    friends=db.scalar(text("SELECT EXISTS(SELECT 1 FROM friendships WHERE user_low_id=:low AND user_high_id=:high)").bindparams(low=low,high=high))
    if not friends: raise HTTPException(403,"Chỉ có thể nhắn tin với bạn bè.")
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:pair))"),{"pair":f"{low}:{high}"})
    cid=db.scalar(text("SELECT c.id FROM conversations c JOIN conversation_members a ON a.conversation_id=c.id AND a.user_id=:a JOIN conversation_members b ON b.conversation_id=c.id AND b.user_id=:b WHERE c.type='DIRECT' AND a.left_at IS NULL AND b.left_at IS NULL LIMIT 1"),{"a":actor.id,"b":target.id})
    if cid:return db.get(Conversation,cid)
    conv=Conversation(type=ConversationType.DIRECT,created_by=actor.id);db.add(conv);db.flush();db.add_all([ConversationMember(conversation_id=conv.id,user_id=actor.id),ConversationMember(conversation_id=conv.id,user_id=target.id)]);db.commit();db.refresh(conv);return conv

def _message(db,m:Message,viewer_id):
    sender=db.get(User,m.sender_id) if m.sender_id else None
    links=db.scalars(select(MessageAttachment).where(MessageAttachment.message_id==m.id)).all();atts=[]
    for link in links:
        media=db.get(MediaFile,link.media_id)
        if media and media.status==MediaStatus.READY:
            atts.append(_attachment(media))
    if m.sender_id==viewer_id:
        receipts=list(db.scalars(select(MessageReceipt).where(MessageReceipt.message_id==m.id)).all())
        status="seen" if receipts and any(r.seen_at for r in receipts) else "delivered" if receipts and all(r.delivered_at for r in receipts) else "sent"
    else:
        receipt=db.get(MessageReceipt,(m.id,viewer_id));status="seen" if receipt and receipt.seen_at else "delivered" if receipt and receipt.delivered_at else "sent"
    return MessageResponse(id=str(m.id),conversationId=str(m.conversation_id),senderId=str(m.sender_id or ""),senderName=sender.profile.full_name if sender and sender.profile else sender.username if sender else "Người dùng",senderAvatar=_avatar(db,sender),content=m.content or "",timestamp=m.created_at.isoformat(),status=status,type="image" if atts and atts[0].type=="image" else "file" if atts else "text",attachments=atts)

def list_messages(db,cid,viewer,limit=50,before=None):
    _member(db,cid,viewer.id);_ensure_not_blocked(db,cid,viewer.id);q=select(Message).where(Message.conversation_id==cid,Message.deleted_at.is_(None));
    if before:q=q.where(Message.created_at<before)
    rows=list(reversed(db.scalars(q.order_by(Message.created_at.desc()).limit(limit)).all()));now=datetime.now(timezone.utc)
    db.execute(text("UPDATE message_receipts r SET delivered_at=COALESCE(delivered_at,:now), seen_at=COALESCE(seen_at,:now) FROM messages m WHERE r.message_id=m.id AND m.conversation_id=:cid AND r.user_id=:uid AND r.seen_at IS NULL"),{"now":now,"cid":cid,"uid":viewer.id});db.commit()
    return [_message(db,m,viewer.id) for m in rows]

def send(db,cid,user,payload:SendMessageRequest):
    from src.services.system_service import enforce_content
    enforce_content(db,payload.content)
    _member(db,cid,user.id);media=list(db.scalars(select(MediaFile).where(MediaFile.id.in_(payload.media_ids))).all()) if payload.media_ids else []
    from src.services.block_service import is_blocked
    other_ids=db.scalars(select(ConversationMember.user_id).where(ConversationMember.conversation_id==cid,ConversationMember.user_id!=user.id,ConversationMember.left_at.is_(None))).all()
    if any(is_blocked(db,user.id,uid) for uid in other_ids):raise HTTPException(403,"Không thể nhắn tin do quan hệ chặn.")
    if len(media)!=len(set(payload.media_ids)) or any(x.owner_id!=user.id or x.status!=MediaStatus.READY for x in media):raise HTTPException(400,"Media tin nhắn không hợp lệ.")
    if payload.reply_to_id:
        reply=db.get(Message,payload.reply_to_id)
        if not reply or reply.conversation_id!=cid:raise HTTPException(400,"Tin nhắn trả lời không hợp lệ.")
    mtype=MessageType.IMAGE if media and all(x.mime_type.startswith("image/") for x in media) else MessageType.FILE if media else MessageType.TEXT
    msg=Message(conversation_id=cid,sender_id=user.id,message_type=mtype,content=payload.content.strip() or None,reply_to_id=payload.reply_to_id);db.add(msg);db.flush()
    for x in media:db.add(MessageAttachment(message_id=msg.id,media_id=x.id))
    recipients=db.scalars(select(ConversationMember.user_id).where(ConversationMember.conversation_id==cid,ConversationMember.user_id!=user.id,ConversationMember.left_at.is_(None))).all();now=datetime.now(timezone.utc)
    from src.services.realtime_service import manager
    for uid in recipients:
        db.add(MessageReceipt(message_id=msg.id,user_id=uid,delivered_at=now if manager.is_online_local(uid) else None))
        recipient_member=db.get(ConversationMember,(cid,uid))
        if not recipient_member or not recipient_member.is_muted:
            db.execute(text("INSERT INTO notifications (user_id,type,title,content,actor_id,reference_type,reference_id) VALUES (:uid,'MESSAGE','Tin nhắn mới',:content,:actor,'CONVERSATION',:ref)"),{"uid":uid,"content":f"{user.profile.full_name if user.profile else user.username} đã gửi cho bạn một tin nhắn.","actor":user.id,"ref":cid})
    conv=db.get(Conversation,cid);conv.last_message_at=now;conv.updated_at=now;db.commit();db.refresh(msg);return _message(db,msg,user.id)

def list_conversations(db,user):
    from src.services.realtime_service import manager
    from src.services.block_service import is_blocked
    ids=db.scalars(select(ConversationMember.conversation_id).where(ConversationMember.user_id==user.id,ConversationMember.left_at.is_(None))).all();result=[]
    for cid in ids:
        conv=db.get(Conversation,cid);other_id=db.scalar(select(ConversationMember.user_id).where(ConversationMember.conversation_id==cid,ConversationMember.user_id!=user.id,ConversationMember.left_at.is_(None)));other=db.get(User,other_id) if other_id else None
        if other_id and is_blocked(db,user.id,other_id):continue
        last=db.scalar(select(Message).where(Message.conversation_id==cid,Message.deleted_at.is_(None)).order_by(Message.created_at.desc()).limit(1));unread=db.scalar(select(func.count()).select_from(MessageReceipt).join(Message,Message.id==MessageReceipt.message_id).where(Message.conversation_id==cid,MessageReceipt.user_id==user.id,MessageReceipt.seen_at.is_(None))) or 0
        viewer_member=db.get(ConversationMember,(cid,user.id));other_member=db.get(ConversationMember,(cid,other_id)) if other_id else None
        display_name=other_member.nickname if other_member and other_member.nickname else other.profile.full_name if other and other.profile else other.username if other else conv.title or "Cuộc trò chuyện"
        result.append(ConversationResponse(id=str(cid),participantId=str(other.id) if other else "",participantName=display_name,participantAvatar=_avatar(db,other),lastMessageSnippet=last.content if last and last.content else "[Media]" if last else "",lastMessageTime=last.created_at.isoformat() if last else conv.created_at.isoformat(),unreadCount=unread,bio=other.profile.bio or "" if other and other.profile else "",role=f"Sinh viên - {other.profile.faculty}" if other and other.profile and other.profile.faculty else "Sinh viên",theme=conv.theme or "blue",nickname=other_member.nickname if other_member else None,isMuted=viewer_member.is_muted if viewer_member else False))
    return sorted(result,key=lambda x:x.lastMessageTime,reverse=True)

def unread_count(db,uid):return db.scalar(select(func.count()).select_from(MessageReceipt).where(MessageReceipt.user_id==uid,MessageReceipt.seen_at.is_(None))) or 0

def update_settings(db:Session,cid:uuid.UUID,user:User,payload:ConversationSettingsRequest):
    member=_member(db,cid,user.id);conv=db.get(Conversation,cid)
    if payload.theme is not None:conv.theme=payload.theme
    if payload.is_muted is not None:member.is_muted=payload.is_muted
    if payload.nickname is not None:
        other=db.scalar(select(ConversationMember).where(ConversationMember.conversation_id==cid,ConversationMember.user_id!=user.id,ConversationMember.left_at.is_(None)))
        if not other:raise HTTPException(400,"Không tìm thấy thành viên để đặt biệt danh.")
        other.nickname=payload.nickname.strip() or None
    db.commit()

def search_messages(db:Session,cid:uuid.UUID,user:User,query:str,limit:int=50):
    _member(db,cid,user.id);_ensure_not_blocked(db,cid,user.id);term=query.strip()
    if not term:return []
    rows=list(reversed(db.scalars(select(Message).where(Message.conversation_id==cid,Message.deleted_at.is_(None),Message.content.ilike(f"%{term}%")).order_by(Message.created_at.desc()).limit(limit)).all()))
    return [_message(db,row,user.id) for row in rows]

def shared_attachments(db:Session,cid:uuid.UUID,user:User,limit:int=100)->SharedAttachmentsResponse:
    _member(db,cid,user.id);_ensure_not_blocked(db,cid,user.id)
    rows=db.scalars(
        select(MediaFile)
        .join(MessageAttachment,MessageAttachment.media_id==MediaFile.id)
        .join(Message,Message.id==MessageAttachment.message_id)
        .where(
            Message.conversation_id==cid,
            Message.deleted_at.is_(None),
            MediaFile.status==MediaStatus.READY,
            MediaFile.deleted_at.is_(None),
        )
        .order_by(Message.created_at.desc(),MediaFile.created_at.desc())
        .limit(limit)
    ).all()
    attachments=[_attachment(media) for media in rows]
    return SharedAttachmentsResponse(
        media=[item for item in attachments if item.type in {"image","video"}],
        files=[item for item in attachments if item.type not in {"image","video"}],
    )
