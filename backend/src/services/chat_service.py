import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import and_, func, select, text
from sqlalchemy.orm import Session
from src.db.models.chat import Conversation,ConversationMember,ConversationType,Message,MessageAttachment,MessageReceipt,MessageType
from src.db.models.media import MediaFile,MediaStatus
from src.db.models.user import Profile, User
from src.models.chat import AttachmentResponse,ConversationResponse,ConversationSettingsRequest,MessageResponse,ReplyMessageResponse,SendMessageRequest,SharedAttachmentsResponse
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
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:pair))"),{"pair":f"{low}:{high}"})
    cid=db.scalar(text("SELECT c.id FROM conversations c JOIN conversation_members a ON a.conversation_id=c.id AND a.user_id=:a JOIN conversation_members b ON b.conversation_id=c.id AND b.user_id=:b WHERE c.type='DIRECT' AND a.left_at IS NULL AND b.left_at IS NULL LIMIT 1"),{"a":actor.id,"b":target.id})
    if cid:return db.get(Conversation,cid)
    conv=Conversation(type=ConversationType.DIRECT,created_by=actor.id);db.add(conv);db.flush();db.add_all([ConversationMember(conversation_id=conv.id,user_id=actor.id),ConversationMember(conversation_id=conv.id,user_id=target.id)]);db.commit();db.refresh(conv);return conv

def _message(db,m:Message,viewer_id):
    return _messages_batch(db,[m],viewer_id)[0]


def _messages_batch(db: Session, rows: list[Message], viewer_id: uuid.UUID) -> list[MessageResponse]:
    if not rows:
        return []
    message_ids = [message.id for message in rows]
    reply_ids = {message.reply_to_id for message in rows if message.reply_to_id}
    replies = {reply.id: reply for reply in db.scalars(select(Message).where(Message.id.in_(reply_ids))).all()} if reply_ids else {}
    sender_ids = {message.sender_id for message in [*rows,*replies.values()] if message.sender_id}
    senders = {user.id: user for user in db.scalars(select(User).where(User.id.in_(sender_ids))).all()} if sender_ids else {}
    profiles = {profile.user_id: profile for profile in db.scalars(select(Profile).where(Profile.user_id.in_(sender_ids))).all()} if sender_ids else {}
    avatar_ids = {profile.avatar_media_id for profile in profiles.values() if profile.avatar_media_id}
    visible_ids = [message.id for message in rows if message.deleted_at is None]
    links = db.scalars(select(MessageAttachment).where(MessageAttachment.message_id.in_(visible_ids))
        .order_by(MessageAttachment.message_id, MessageAttachment.media_id)).all()
    media_ids = avatar_ids | {link.media_id for link in links}
    media_by_id = {media.id: media for media in db.scalars(select(MediaFile).where(
        MediaFile.id.in_(media_ids), MediaFile.status == MediaStatus.READY
    )).all()} if media_ids else {}
    attachments: dict[uuid.UUID, list[AttachmentResponse]] = {message_id: [] for message_id in message_ids}
    for link in links:
        media = media_by_id.get(link.media_id)
        if media:
            attachments[link.message_id].append(_attachment(media))
    receipts: dict[uuid.UUID, list[MessageReceipt]] = {message_id: [] for message_id in message_ids}
    for receipt in db.scalars(select(MessageReceipt).where(MessageReceipt.message_id.in_(message_ids))).all():
        receipts[receipt.message_id].append(receipt)

    result = []
    for message in rows:
        sender = senders.get(message.sender_id)
        profile = profiles.get(message.sender_id)
        avatar_media = media_by_id.get(profile.avatar_media_id) if profile and profile.avatar_media_id else None
        recalled = message.deleted_at is not None
        files = [] if recalled else attachments[message.id]
        reply = replies.get(message.reply_to_id)
        reply_sender = senders.get(reply.sender_id) if reply else None
        reply_profile = profiles.get(reply.sender_id) if reply else None
        message_receipts = receipts[message.id]
        if message.sender_id == viewer_id:
            status = ("seen" if message_receipts and any(receipt.seen_at for receipt in message_receipts) else
                      "delivered" if message_receipts and all(receipt.delivered_at for receipt in message_receipts) else "sent")
        else:
            viewer_receipt = next((receipt for receipt in message_receipts if receipt.user_id == viewer_id), None)
            status = "seen" if viewer_receipt and viewer_receipt.seen_at else "delivered" if viewer_receipt and viewer_receipt.delivered_at else "sent"
        result.append(MessageResponse(
            id=str(message.id), conversationId=str(message.conversation_id), senderId=str(message.sender_id or ""),
            senderName=profile.full_name if profile else sender.username if sender else "Người dùng",
            senderAvatar=create_download_url(avatar_media) if avatar_media else "/assets/logo.png",
            content="Tin nhắn đã được thu hồi" if recalled else message.content or "", timestamp=message.created_at.isoformat(), status=status,
            type="image" if files and files[0].type == "image" else "file" if files else "text",
            attachments=files,
            isRecalled=recalled,
            replyTo=ReplyMessageResponse(
                id=str(reply.id), senderName=reply_profile.full_name if reply_profile else reply_sender.username if reply_sender else "Người dùng",
                content="Tin nhắn đã được thu hồi" if reply.deleted_at is not None else reply.content or "[Tệp đính kèm]",
                isRecalled=reply.deleted_at is not None,
            ) if reply else None,
        ))
    return result

def list_messages(db,cid,viewer,limit=50,before=None):
    _member(db,cid,viewer.id);_ensure_not_blocked(db,cid,viewer.id);q=select(Message).where(Message.conversation_id==cid);
    if before:q=q.where(Message.created_at<before)
    rows=list(reversed(db.scalars(q.order_by(Message.created_at.desc()).limit(limit)).all()));now=datetime.now(timezone.utc)
    db.execute(text("UPDATE message_receipts r SET delivered_at=COALESCE(delivered_at,:now), seen_at=COALESCE(seen_at,:now) FROM messages m WHERE r.message_id=m.id AND m.conversation_id=:cid AND r.user_id=:uid AND r.seen_at IS NULL"),{"now":now,"cid":cid,"uid":viewer.id})
    result = _messages_batch(db, rows, viewer.id)
    db.commit()
    return result

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
        if not reply or reply.conversation_id!=cid or reply.deleted_at is not None:raise HTTPException(400,"Tin nhắn trả lời không hợp lệ.")
    mtype=MessageType.IMAGE if media and all(x.mime_type.startswith("image/") for x in media) else MessageType.FILE if media else MessageType.TEXT
    msg=Message(conversation_id=cid,sender_id=user.id,message_type=mtype,content=payload.content.strip() or None,reply_to_id=payload.reply_to_id);db.add(msg);db.flush()
    for x in media:db.add(MessageAttachment(message_id=msg.id,media_id=x.id))
    recipients=db.scalars(select(ConversationMember.user_id).where(ConversationMember.conversation_id==cid,ConversationMember.user_id!=user.id,ConversationMember.left_at.is_(None))).all();now=datetime.now(timezone.utc)
    from src.services.realtime_service import manager
    for uid in recipients:
        db.add(MessageReceipt(message_id=msg.id,user_id=uid,delivered_at=now if manager.is_online_local(uid) else None))
        recipient_member=db.get(ConversationMember,(cid,uid))
        # Message events are handled by the chat badge, not the notification center.
        if False and (not recipient_member or not recipient_member.is_muted):
            db.execute(text("INSERT INTO notifications (user_id,type,title,content,actor_id,reference_type,reference_id) VALUES (:uid,'MESSAGE','Tin nhắn mới',:content,:actor,'CONVERSATION',:ref)"),{"uid":uid,"content":f"{user.profile.full_name if user.profile else user.username} đã gửi cho bạn một tin nhắn.","actor":user.id,"ref":cid})
    conv=db.get(Conversation,cid);conv.last_message_at=now;conv.updated_at=now;db.commit();db.refresh(msg);return _message(db,msg,user.id)

def recall(db:Session,cid:uuid.UUID,message_id:uuid.UUID,user:User)->MessageResponse:
    _member(db,cid,user.id)
    _ensure_not_blocked(db,cid,user.id)
    message=db.get(Message,message_id)
    if not message or message.conversation_id!=cid:raise HTTPException(404,"Không tìm thấy tin nhắn.")
    if message.sender_id!=user.id:raise HTTPException(403,"Bạn chỉ có thể thu hồi tin nhắn của mình.")
    if message.deleted_at is not None:raise HTTPException(409,"Tin nhắn đã được thu hồi.")
    message.deleted_at=datetime.now(timezone.utc)
    message.content=None
    db.commit()
    db.refresh(message)
    return _message(db,message,user.id)

def list_conversations(db,user):
    viewer_members = db.scalars(select(ConversationMember).where(
        ConversationMember.user_id == user.id, ConversationMember.left_at.is_(None)
    )).all()
    if not viewer_members:
        return []
    ids = [member.conversation_id for member in viewer_members]
    viewer_by_conversation = {member.conversation_id: member for member in viewer_members}
    conversations = {conv.id: conv for conv in db.scalars(select(Conversation).where(Conversation.id.in_(ids))).all()}
    other_members = db.scalars(select(ConversationMember).where(
        ConversationMember.conversation_id.in_(ids), ConversationMember.user_id != user.id,
        ConversationMember.left_at.is_(None)
    )).all()
    other_by_conversation = {}
    for member in other_members:
        other_by_conversation.setdefault(member.conversation_id, member)
    other_ids = {member.user_id for member in other_by_conversation.values()}
    others, profiles, avatars = {}, {}, {}
    if other_ids:
        peer_rows = db.execute(
            select(User, Profile, MediaFile)
            .outerjoin(Profile, Profile.user_id == User.id)
            .outerjoin(MediaFile, and_(
                MediaFile.id == Profile.avatar_media_id,
                MediaFile.status == MediaStatus.READY,
            ))
            .where(User.id.in_(other_ids))
        ).all()
        for peer, profile, avatar in peer_rows:
            others[peer.id] = peer
            if profile:
                profiles[peer.id] = profile
            if avatar:
                avatars[avatar.id] = avatar
    blocked_ids = set(db.scalars(text(
        "SELECT CASE WHEN blocker_id=:uid THEN blocked_id ELSE blocker_id END "
        "FROM user_blocks WHERE blocker_id=:uid OR blocked_id=:uid"
    ), {"uid": user.id}).all())

    ranked = select(Message.id.label("message_id"), func.row_number().over(
        partition_by=Message.conversation_id, order_by=Message.created_at.desc()
    ).label("rank")).where(Message.conversation_id.in_(ids)).subquery()
    last_messages = {item.conversation_id: item for item in db.scalars(
        select(Message).join(ranked, Message.id == ranked.c.message_id).where(ranked.c.rank == 1)
    ).all()}
    unread = dict(db.execute(select(Message.conversation_id, func.count()).select_from(MessageReceipt)
        .join(Message, Message.id == MessageReceipt.message_id)
        .where(Message.conversation_id.in_(ids), MessageReceipt.user_id == user.id,
               MessageReceipt.seen_at.is_(None), Message.deleted_at.is_(None))
        .group_by(Message.conversation_id)).all())
    result = []
    for cid in ids:
        conv = conversations.get(cid)
        if conv is None:
            continue
        other_member = other_by_conversation.get(cid)
        other_id = other_member.user_id if other_member else None
        if other_id in blocked_ids:
            continue
        other = others.get(other_id)
        profile = profiles.get(other_id)
        avatar_media = avatars.get(profile.avatar_media_id) if profile and profile.avatar_media_id else None
        last = last_messages.get(cid)
        display_name = (other_member.nickname if other_member and other_member.nickname else
                        profile.full_name if profile else other.username if other else conv.title or "Cuộc trò chuyện")
        result.append(ConversationResponse(
            id=str(cid), participantId=str(other.id) if other else "", participantName=display_name,
            participantAvatar=create_download_url(avatar_media) if avatar_media else "/assets/logo.png",
            lastMessageSnippet="Tin nhắn đã được thu hồi" if last and last.deleted_at is not None else last.content if last and last.content else "[Media]" if last else "",
            lastMessageTime=last.created_at.isoformat() if last else conv.created_at.isoformat(),
            unreadCount=unread.get(cid, 0), bio=profile.bio or "" if profile else "",
            role=f"Sinh viên - {profile.faculty}" if profile and profile.faculty else "Sinh viên",
            theme=conv.theme or "blue", nickname=other_member.nickname if other_member else None,
            isMuted=viewer_by_conversation[cid].is_muted,
        ))
    return sorted(result, key=lambda item: item.lastMessageTime, reverse=True)

def unread_count(db,uid):return db.scalar(select(func.count()).select_from(MessageReceipt).join(Message,Message.id==MessageReceipt.message_id).where(MessageReceipt.user_id==uid,MessageReceipt.seen_at.is_(None),Message.deleted_at.is_(None))) or 0

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
    return _messages_batch(db, rows, user.id)

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
