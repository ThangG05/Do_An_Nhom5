"""Compatibility alias for AI conversation; social chat lives in app.models.chat."""
from app.models.rag import AIConversation

Conversation = AIConversation

__all__ = ["Conversation"]
