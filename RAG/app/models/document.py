"""Compatibility aliases; use the AI-prefixed model names in new code."""
from app.models.rag import AIDocument, AIDocumentChunk, AIDocumentVersion

Document = AIDocument
DocumentVersion = AIDocumentVersion
DocumentChunk = AIDocumentChunk

__all__ = ["Document", "DocumentVersion", "DocumentChunk"]
