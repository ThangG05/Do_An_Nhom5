from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from app.schemas.rag import RAGCitationResponse


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=500)


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=500)


class ConversationResponse(BaseModel):
    id: UUID
    title: str | None
    academic_year_context: str | None
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ConversationMessageResponse(BaseModel):
    id: UUID
    sequence_number: int
    role: str
    content: str
    rewritten_question: str | None
    created_at: datetime
    citations: list[RAGCitationResponse] = Field(default_factory=list)


class ConversationMessagesResponse(BaseModel):
    conversation: ConversationResponse
    messages: list[ConversationMessageResponse]
