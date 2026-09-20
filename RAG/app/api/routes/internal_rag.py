import secrets
from dataclasses import asdict
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import get_settings
from app.db.session import get_db
from app.llm.contracts import LLMConfigurationError, LLMServiceError
from app.llm.security import PromptSecurityError
from app.rag.embeddings import EmbeddingError, get_embedding_provider
from app.rag.retriever import RetrievalService
from app.rag.service import RAGService
from app.schemas.rag import InternalRAGRequest, InternalRAGResponse, RAGCitationResponse
from app.services.llm import get_llm_provider

router = APIRouter(prefix="/internal/rag")


@router.post("/ask", response_model=InternalRAGResponse, include_in_schema=False)
async def ask_rag(request: InternalRAGRequest, internal_key: str | None = Header(default=None, alias="X-Internal-API-Key"),
                  session: AsyncSession = Depends(get_db)) -> InternalRAGResponse:
    settings = get_settings()
    if not settings.internal_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Internal endpoint disabled")
    if not internal_key or not secrets.compare_digest(internal_key, settings.internal_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        embedder = get_embedding_provider()
        result = await RAGService(session, RetrievalService(embedder, session), get_llm_provider()).ask(
            request.question, request.conversation_id)
    except PromptSecurityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.code) from None
    except ValueError as exc:
        code = status.HTTP_404_NOT_FOUND if "conversation" in str(exc) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc)) from None
    except (EmbeddingError, LLMConfigurationError, LLMServiceError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG service unavailable") from None
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Knowledge database temporarily unavailable") from None
    return InternalRAGResponse(conversation_id=result.conversation_id, message_id=result.message_id,
        answer=result.answer, refused=result.refused, refusal_reason=result.refusal_reason,
        citations=[RAGCitationResponse(**asdict(citation)) for citation in result.citations],
        rewritten_question=result.rewritten_question)
