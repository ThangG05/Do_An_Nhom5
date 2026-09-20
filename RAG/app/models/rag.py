from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AIDocumentStatus, AIDocumentType, AIMessageRole, AIVisibility


class AIDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_documents"
    document_code: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(500))
    document_type: Mapped[AIDocumentType] = mapped_column(Enum(AIDocumentType, name="ai_document_type"), default=AIDocumentType.OTHER)
    academic_year: Mapped[str | None] = mapped_column(String(9))
    issuer: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    visibility: Mapped[AIVisibility] = mapped_column(Enum(AIVisibility, name="ai_visibility"), default=AIVisibility.PUBLIC)
    group_id: Mapped[UUID | None] = mapped_column(ForeignKey("groups.id", ondelete="SET NULL"))
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    current_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("ai_document_versions.id", ondelete="SET NULL", use_alter=True, name="fk_ai_current_version"))
    is_current: Mapped[bool] = mapped_column(default=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("academic_year IS NULL OR academic_year ~ '^[0-9]{4}/[0-9]{4}$'", name="ck_ai_academic_year"),
        CheckConstraint("effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from", name="ck_ai_effective_period"),
        Index("idx_ai_documents_retrieval", "document_type", "academic_year", "is_current",
              text("published_at DESC")),
        Index("idx_ai_documents_metadata", "metadata", postgresql_using="gin"),
    )


class AIDocumentVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_document_versions"
    document_id: Mapped[UUID] = mapped_column(ForeignKey("ai_documents.id", ondelete="RESTRICT"))
    version_number: Mapped[int]
    version_label: Mapped[str | None] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    source_url: Mapped[str | None] = mapped_column(Text)
    file_object_key: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    content_hash: Mapped[str] = mapped_column(String(64))
    raw_content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[AIDocumentStatus] = mapped_column(Enum(AIDocumentStatus, name="ai_document_status"), default=AIDocumentStatus.PENDING)
    error_message: Mapped[str | None] = mapped_column(Text)
    embedding_model: Mapped[str | None] = mapped_column(String(255))
    chunking_version: Mapped[str | None] = mapped_column(String(50))
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_ai_document_version"),
        UniqueConstraint("document_id", "content_hash", name="uq_ai_document_hash"),
        CheckConstraint("version_number > 0", name="ck_ai_version_positive"),
        CheckConstraint("source_url IS NOT NULL OR file_object_key IS NOT NULL", name="ck_ai_source"),
        Index("idx_ai_versions_status", "status", "created_at"),
    )


class AIDocumentChunk(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_document_chunks"
    document_version_id: Mapped[UUID] = mapped_column(ForeignKey("ai_document_versions.id", ondelete="RESTRICT"))
    chunk_index: Mapped[int]
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    token_count: Mapped[int]
    page_start: Mapped[int | None]
    page_end: Mapped[int | None]
    section_title: Mapped[str | None] = mapped_column(String(500))
    heading_path: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    start_offset: Mapped[int | None]
    end_offset: Mapped[int | None]
    qdrant_point_id: Mapped[UUID] = mapped_column(default=uuid4)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    __table_args__ = (
        UniqueConstraint("document_version_id", "chunk_index", name="uq_ai_chunk_index"),
        UniqueConstraint("qdrant_point_id", name="uq_ai_qdrant_point"),
        CheckConstraint("chunk_index >= 0", name="ck_ai_chunk_index"),
        CheckConstraint("token_count > 0", name="ck_ai_chunk_tokens"),
        CheckConstraint("page_end IS NULL OR page_start IS NULL OR page_end >= page_start", name="ck_ai_chunk_pages"),
        Index("idx_ai_chunks_version", "document_version_id", "chunk_index"),
    )


class AIDocumentRelation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_document_relations"
    source_document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_document_versions.id", ondelete="CASCADE")
    )
    target_document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ai_documents.id", ondelete="SET NULL")
    )
    referenced_number: Mapped[str] = mapped_column(String(100))
    relation_type: Mapped[str] = mapped_column(String(30), default="REFERENCES")
    context_excerpt: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    __table_args__ = (
        UniqueConstraint("source_document_version_id", "referenced_number", "relation_type",
                         name="uq_ai_document_relation"),
        CheckConstraint(
            "relation_type IN ('REFERENCES','AMENDS','SUPERSEDES','REPEALS')",
            name="ck_ai_document_relation_type",
        ),
        Index("idx_ai_document_relations_source", "source_document_version_id"),
        Index("idx_ai_document_relations_target", "target_document_id"),
        Index("idx_ai_document_relations_number", "referenced_number"),
    )


class AIConversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_conversations"
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    title: Mapped[str | None] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text)
    summary_until_sequence: Mapped[int] = mapped_column(default=0)
    academic_year_context: Mapped[str | None] = mapped_column(String(9))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("academic_year_context IS NULL OR academic_year_context ~ '^[0-9]{4}/[0-9]{4}$'", name="ck_ai_conversation_year"),
        Index("idx_ai_conversations_user", "user_id", text("updated_at DESC")),
    )


class AIMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_messages"
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("ai_conversations.id", ondelete="CASCADE"))
    sequence_number: Mapped[int]
    role: Mapped[AIMessageRole] = mapped_column(Enum(AIMessageRole, name="ai_message_role"))
    content: Mapped[str] = mapped_column(Text)
    rewritten_question: Mapped[str | None] = mapped_column(Text)
    retrieval_filters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    model_name: Mapped[str | None] = mapped_column(String(255))
    prompt_tokens: Mapped[int | None]
    completion_tokens: Mapped[int | None]
    latency_ms: Mapped[int | None]
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    __table_args__ = (UniqueConstraint("conversation_id", "sequence_number", name="uq_ai_message_sequence"),
                      CheckConstraint("sequence_number > 0", name="ck_ai_message_sequence"),
                      Index("idx_ai_messages_history", "conversation_id", "sequence_number"))


class AIMessageCitation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_message_citations"
    message_id: Mapped[UUID] = mapped_column(ForeignKey("ai_messages.id", ondelete="CASCADE"))
    chunk_id: Mapped[UUID] = mapped_column(ForeignKey("ai_document_chunks.id", ondelete="RESTRICT"))
    citation_order: Mapped[int]
    retrieval_rank: Mapped[int | None]
    relevance_score: Mapped[float | None] = mapped_column(Float)
    quoted_text: Mapped[str | None] = mapped_column(Text)
    document_title_snapshot: Mapped[str] = mapped_column(String(500))
    source_url_snapshot: Mapped[str | None] = mapped_column(Text)
    source_label_snapshot: Mapped[str | None] = mapped_column(String(255))
    page_start_snapshot: Mapped[int | None]
    page_end_snapshot: Mapped[int | None]
    section_title_snapshot: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    __table_args__ = (UniqueConstraint("message_id", "citation_order", name="uq_ai_citation_order"),
                      UniqueConstraint("message_id", "chunk_id", name="uq_ai_citation_chunk"),
                      CheckConstraint("citation_order > 0", name="ck_ai_citation_order"),
                      Index("idx_ai_citations_message", "message_id", "citation_order"))
