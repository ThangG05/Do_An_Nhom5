from app.db.base import Base
from app.models import AIConversation, AIDocument, AIMessage, Conversation, Message


def test_expected_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "users", "profiles", "roles", "user_roles", "email_verification_codes",
        "refresh_tokens", "groups", "group_members", "posts", "media_files",
        "post_media", "comments", "post_likes", "reports", "friend_requests",
        "friendships", "user_blocks", "conversations", "conversation_members",
        "messages", "message_attachments", "message_receipts", "notifications",
        "ai_documents", "ai_document_versions", "ai_document_chunks", "ai_document_relations",
        "ai_conversations", "ai_messages", "ai_message_citations", "audit_logs",
        "ai_sources", "ai_source_urls", "ai_crawl_runs", "ai_crawl_items",
    }
    assert Conversation.__tablename__ == "conversations"
    assert Message.__tablename__ == "messages"
    assert AIDocument.__tablename__ == "ai_documents"
    assert AIConversation.__tablename__ == "ai_conversations"
    assert AIMessage.__tablename__ == "ai_messages"


def test_social_and_ai_conversations_are_separate() -> None:
    assert Conversation.__table__ is not AIConversation.__table__
    assert Message.__table__ is not AIMessage.__table__
