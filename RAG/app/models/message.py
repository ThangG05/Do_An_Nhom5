"""Compatibility aliases for AI messages; social messages live in app.models.chat."""
from app.models.enums import AIMessageRole
from app.models.rag import AIMessage, AIMessageCitation

Message = AIMessage
MessageCitation = AIMessageCitation
MessageRole = AIMessageRole

__all__ = ["Message", "MessageCitation", "MessageRole"]
