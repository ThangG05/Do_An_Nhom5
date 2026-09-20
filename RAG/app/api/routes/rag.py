import asyncio
from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.llm.contracts import LLMConfigurationError, LLMServiceError
from app.llm.security import PromptSecurityError
from app.models.audit import AuditLog
from app.models.auth import User
from app.models.community import GroupMember
from app.rag.embeddings import EmbeddingError, get_embedding_provider
from app.rag.retriever import AccessScope, RetrievalService
from app.rag.service import RAGService
from app.schemas.rag import InternalRAGRequest, InternalRAGResponse, RAGCitationResponse
from app.services.llm import get_llm_provider
from app.services.rate_limit import (ConcurrencyLimitExceeded, RateLimitExceeded,
                                     acquire_rag_slot, enforce_rag_rate_limit,
                                     release_rag_slot)

router = APIRouter(prefix="/rag")


@router.post("/chat", response_model=InternalRAGResponse, summary="Grounded HVNH assistant")
async def chat(request_body: InternalRAGRequest, request: Request,
               user: User = Depends(get_current_user),
               session: AsyncSession = Depends(get_db)) -> InternalRAGResponse:
    client_ip = request.client.host if request.client else "unknown"
    try:
        await asyncio.gather(
            enforce_rag_rate_limit(f"user:{user.id}"),
            enforce_rag_rate_limit(f"ip:{client_ip}"),
        )
    except RateLimitExceeded:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Too many requests", headers={"Retry-After": "60"}) from None
    except RedisError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Rate limiter unavailable") from None
    group_ids = tuple((await session.scalars(select(GroupMember.group_id).where(
        GroupMember.user_id == user.id))).all())
    slot_token = None
    try:
        slot_token = await acquire_rag_slot()
        embedder = get_embedding_provider()
        result = await RAGService(session, RetrievalService(embedder, session), get_llm_provider()).ask(
            request_body.question, request_body.conversation_id,
            access=AccessScope(authenticated=True, group_ids=group_ids), user_id=user.id)
    except PromptSecurityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.code) from None
    except ValueError as exc:
        code = status.HTTP_404_NOT_FOUND if "conversation" in str(exc) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc)) from None
    except (EmbeddingError, LLMConfigurationError, LLMServiceError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="RAG service unavailable") from None
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Knowledge database temporarily unavailable") from None
    except ConcurrencyLimitExceeded:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="RAG service busy", headers={"Retry-After": "5"}) from None
    except RedisError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="RAG coordination unavailable") from None
    finally:
        if slot_token is not None:
            try: await release_rag_slot(slot_token)
            except RedisError: pass
    try:
        session.add(AuditLog(actor_id=user.id, action="RAG_CHAT", target_type="AI_MESSAGE",
            target_id=result.message_id, ip_address=client_ip,
            metadata_={"refused": result.refused, "citation_count": len(result.citations)}))
        await session.commit()
    except Exception:
        await session.rollback()  # Audit failure must not discard an already committed answer.
    return InternalRAGResponse(conversation_id=result.conversation_id, message_id=result.message_id,
        answer=result.answer, refused=result.refused, refusal_reason=result.refusal_reason,
        rewritten_question=result.rewritten_question,
        citations=[RAGCitationResponse(**asdict(item)) for item in result.citations])
