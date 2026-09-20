from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import FriendRequestStatus


class FriendRequest(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "friend_requests"
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    receiver_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[FriendRequestStatus] = mapped_column(
        Enum(FriendRequestStatus, name="friend_request_status"), default=FriendRequestStatus.PENDING)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    __table_args__ = (
        CheckConstraint("sender_id <> receiver_id", name="ck_friend_request_distinct"),
        Index("uq_pending_friend_pair", func.least(sender_id, receiver_id),
              func.greatest(sender_id, receiver_id), unique=True,
              postgresql_where=text("status = 'PENDING'")),
    )


class Friendship(Base):
    __tablename__ = "friendships"
    user_low_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    user_high_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    __table_args__ = (CheckConstraint("user_low_id < user_high_id", name="ck_friendship_order"),
                      Index("idx_friendships_high", "user_high_id"))


class UserBlock(Base):
    __tablename__ = "user_blocks"
    blocker_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    blocked_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    __table_args__ = (CheckConstraint("blocker_id <> blocked_id", name="ck_user_block_distinct"),)
