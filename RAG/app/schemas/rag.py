from uuid import UUID
from pydantic import BaseModel, Field


class InternalRAGRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None


class RAGCitationResponse(BaseModel):
    order: int
    title: str
    source_url: str | None
    page_start: int | None
    page_end: int | None
    section_title: str | None
    relevance_score: float


class InternalRAGResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    answer: str
    refused: bool
    refusal_reason: str | None
    citations: list[RAGCitationResponse]
    rewritten_question: str
