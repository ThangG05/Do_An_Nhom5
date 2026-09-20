import enum, uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, PrimaryKeyConstraint, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import Base

class ConversationType(str, enum.Enum): DIRECT="DIRECT"; GROUP="GROUP"
class MessageType(str, enum.Enum): TEXT="TEXT"; IMAGE="IMAGE"; FILE="FILE"; SYSTEM="SYSTEM"

class Conversation(Base):
    __tablename__="conversations"
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    type: Mapped[ConversationType]=mapped_column(Enum(ConversationType,name="conversation_type"),nullable=False,default=ConversationType.DIRECT)
    title: Mapped[str|None]=mapped_column(String(255)); theme: Mapped[str]=mapped_column(String(30),nullable=False,default="blue",server_default="blue"); created_by: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="SET NULL"))
    last_message_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)

class ConversationMember(Base):
    __tablename__="conversation_members"; __table_args__=(PrimaryKeyConstraint("conversation_id","user_id",name="conversation_members_pkey"),)
    conversation_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("conversations.id",ondelete="CASCADE")); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE")); nickname: Mapped[str|None]=mapped_column(String(100)); is_muted: Mapped[bool]=mapped_column(Boolean,nullable=False,default=False,server_default="false"); joined_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False); left_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class Message(Base):
    __tablename__="messages"
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); conversation_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("conversations.id",ondelete="CASCADE"),nullable=False); sender_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="SET NULL")); message_type: Mapped[MessageType]=mapped_column(Enum(MessageType,name="message_type"),nullable=False,default=MessageType.TEXT); content: Mapped[str|None]=mapped_column(Text); reply_to_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("messages.id",ondelete="SET NULL")); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False); edited_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); deleted_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class MessageAttachment(Base):
    __tablename__="message_attachments"; __table_args__=(PrimaryKeyConstraint("message_id","media_id",name="message_attachments_pkey"),)
    message_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("messages.id",ondelete="CASCADE")); media_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("media_files.id",ondelete="CASCADE"))

class MessageReceipt(Base):
    __tablename__="message_receipts"; __table_args__=(PrimaryKeyConstraint("message_id","user_id",name="message_receipts_pkey"),)
    message_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("messages.id",ondelete="CASCADE")); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE")); delivered_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); seen_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
