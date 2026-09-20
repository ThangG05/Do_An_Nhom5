from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.rag import AIConversation, AIMessage, AIMessageCitation
from app.schemas.conversation import (
    ConversationCreate, ConversationMessageResponse, ConversationMessagesResponse,
    ConversationResponse, ConversationUpdate,
)
from app.schemas.rag import RAGCitationResponse

router = APIRouter(prefix="/conversations")


def _conversation_response(row: AIConversation) -> ConversationResponse:
    return ConversationResponse(
        id=row.id, title=row.title, academic_year_context=row.academic_year_context,
        last_message_at=row.last_message_at, created_at=row.created_at, updated_at=row.updated_at,
    )


async def _owned(session: AsyncSession, conversation_id: UUID, user_id: UUID,
                 *, lock: bool = False) -> AIConversation:
    statement = select(AIConversation).where(
        AIConversation.id == conversation_id,
        AIConversation.user_id == user_id,
        AIConversation.deleted_at.is_(None),
    )
    if lock:
        statement = statement.with_for_update()
    row = await session.scalar(statement)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return row


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(body: ConversationCreate, user: User = Depends(get_current_user),
                              session: AsyncSession = Depends(get_db)) -> ConversationResponse:
    row = AIConversation(user_id=user.id, title=body.title, metadata_={"channel": "public_rag"})
    session.add(row); await session.commit(); await session.refresh(row)
    return _conversation_response(row)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(limit: int = Query(default=30, ge=1, le=100),
                             offset: int = Query(default=0, ge=0),
                             user: User = Depends(get_current_user),
                             session: AsyncSession = Depends(get_db)) -> list[ConversationResponse]:
    rows = (await session.scalars(select(AIConversation).where(
        AIConversation.user_id == user.id, AIConversation.deleted_at.is_(None),
    ).order_by(AIConversation.last_message_at.desc().nullslast(), AIConversation.created_at.desc())
      .offset(offset).limit(limit))).all()
    return [_conversation_response(row) for row in rows]


@router.get("/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def conversation_messages(conversation_id: UUID,
                                limit: int = Query(default=100, ge=1, le=500),
                                before_sequence: int | None = Query(default=None, ge=1),
                                user: User = Depends(get_current_user),
                                session: AsyncSession = Depends(get_db)) -> ConversationMessagesResponse:
    conversation = await _owned(session, conversation_id, user.id)
    statement = select(AIMessage).where(AIMessage.conversation_id == conversation.id)
    if before_sequence is not None:
        statement = statement.where(AIMessage.sequence_number < before_sequence)
    rows = list((await session.scalars(
        statement.order_by(AIMessage.sequence_number.desc()).limit(limit)
    )).all())
    rows.reverse()
    citation_map: dict[UUID, list[RAGCitationResponse]] = {}
    if rows:
        citation_rows = (await session.scalars(select(AIMessageCitation).where(
            AIMessageCitation.message_id.in_([row.id for row in rows])
        ).order_by(AIMessageCitation.message_id, AIMessageCitation.citation_order))).all()
        for citation in citation_rows:
            citation_map.setdefault(citation.message_id, []).append(RAGCitationResponse(
                order=citation.citation_order,
                title=citation.document_title_snapshot,
                source_url=citation.source_url_snapshot,
                page_start=citation.page_start_snapshot,
                page_end=citation.page_end_snapshot,
                section_title=citation.section_title_snapshot,
                relevance_score=citation.relevance_score or 0.0,
            ))
    return ConversationMessagesResponse(
        conversation=_conversation_response(conversation),
        messages=[ConversationMessageResponse(
            id=row.id, sequence_number=row.sequence_number, role=row.role.value,
            content=row.content, rewritten_question=row.rewritten_question, created_at=row.created_at,
            citations=citation_map.get(row.id, []),
        ) for row in rows],
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def rename_conversation(conversation_id: UUID, body: ConversationUpdate,
                              user: User = Depends(get_current_user),
                              session: AsyncSession = Depends(get_db)) -> ConversationResponse:
    row = await _owned(session, conversation_id, user.id, lock=True)
    row.title = body.title.strip(); await session.commit(); await session.refresh(row)
    return _conversation_response(row)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: UUID, user: User = Depends(get_current_user),
                              session: AsyncSession = Depends(get_db)) -> Response:
    from datetime import UTC, datetime
    row = await _owned(session, conversation_id, user.id, lock=True)
    row.deleted_at = datetime.now(UTC); await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
