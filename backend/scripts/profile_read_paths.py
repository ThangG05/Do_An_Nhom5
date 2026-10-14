"""Read-only latency/round-trip probe for representative API service paths.

Run from backend/: python -m scripts.profile_read_paths
Only aggregate timings and query counts are printed; no user data is logged.
"""

from time import perf_counter
import sys

from sqlalchemy import event, select, text
from sqlalchemy.orm import Session

from src.db.models.chat import Message
from src.db.models.user import User
from src.db.session import engine
from src.services import chat_service, notification_service, post_service


def profile(label: str, db: Session, work) -> list:
    starts: list[float] = []
    durations: list[float] = []

    def before(_conn, _cursor, _statement, _parameters, _context, _many):
        starts.append(perf_counter())

    def after(_conn, _cursor, _statement, _parameters, _context, _many):
        durations.append((perf_counter() - starts.pop()) * 1000)

    event.listen(engine, "before_cursor_execute", before)
    event.listen(engine, "after_cursor_execute", after)
    start = perf_counter()
    try:
        result = work()
        print(f"{label}: rows={len(result)} queries={len(durations)} "
              f"elapsed_ms={(perf_counter() - start) * 1000:.0f} "
              f"sql_ms={sum(durations):.0f}")
        return result
    finally:
        event.remove(engine, "before_cursor_execute", before)
        event.remove(engine, "after_cursor_execute", after)


def main() -> None:
    with Session(engine) as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        sample_user_id = db.scalar(select(User.id).where(User.deleted_at.is_(None)).limit(1))
        chat_user_id = db.scalar(text(
            "SELECT user_id FROM conversation_members GROUP BY user_id "
            "ORDER BY count(*) DESC LIMIT 1"
        ))
        notification_user_id = db.scalar(text(
            "SELECT user_id FROM notifications GROUP BY user_id "
            "ORDER BY count(*) DESC LIMIT 1"
        ))
        if sample_user_id:
            user = db.get(User, sample_user_id)
            profile("feed_10", db, lambda: post_service.list_feed(db, user, limit=10)[0])
        if chat_user_id:
            user = db.get(User, chat_user_id)
            profile("conversations", db, lambda: chat_service.list_conversations(db, user))
            conversation_id = db.scalar(text(
                "SELECT conversation_id FROM conversation_members WHERE user_id=:uid "
                "ORDER BY (SELECT count(*) FROM messages WHERE conversation_id=conversation_members.conversation_id) DESC LIMIT 1"
            ), {"uid": chat_user_id})
            if conversation_id:
                messages = list(reversed(db.scalars(select(Message).where(
                    Message.conversation_id == conversation_id, Message.deleted_at.is_(None)
                ).order_by(Message.created_at.desc()).limit(50)).all()))
                cards = profile("message_cards", db, lambda: chat_service._messages_batch(db, messages, user.id))
                if "--legacy-messages" in sys.argv:
                    legacy = profile("message_cards_legacy", db, lambda: [
                        chat_service._message(db, message, user.id) for message in messages
                    ])
                    fields = ("id", "conversationId", "senderId", "senderName", "content", "timestamp", "status", "type")
                    equivalent = all(
                        all(getattr(new, field) == getattr(old, field) for field in fields)
                        and [(file.id, file.type, file.name, file.size) for file in new.attachments]
                        == [(file.id, file.type, file.name, file.size) for file in old.attachments]
                        for new, old in zip(cards, legacy)
                    ) and len(cards) == len(legacy)
                    print("message_cards_equivalent", equivalent)
        if notification_user_id:
            user = db.get(User, notification_user_id)
            profile("notifications_30", db, lambda: notification_service.list_notifications(
                db, user, 30, 0
            ).items)
        db.rollback()


if __name__ == "__main__":
    main()
