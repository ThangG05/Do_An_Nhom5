import secrets

from fastapi import APIRouter, Header, HTTPException, status

from app.core.config import get_settings
from app.llm.contracts import ContextBlock
from app.schemas.llm import InternalLLMTestResponse
from app.services.llm import LLMConfigurationError, LLMServiceError, get_llm_provider


router = APIRouter(prefix="/internal/llm")


@router.post("/test", response_model=InternalLLMTestResponse, include_in_schema=False)
async def test_llm_provider(
    internal_key: str | None = Header(default=None, alias="X-Internal-API-Key"),
) -> InternalLLMTestResponse:
    settings = get_settings()
    if not settings.internal_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Internal endpoint disabled")
    if not internal_key or not secrets.compare_digest(internal_key, settings.internal_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        result = await get_llm_provider().answer(
            "Tên hệ thống trong nguồn được cung cấp là gì?",
            [ContextBlock(
                id="internal-health-check",
                source_label="Internal health check",
                content="Tên hệ thống là HVNH Hub.",
            )],
        )
    except (LLMConfigurationError, LLMServiceError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM unavailable") from None
    return InternalLLMTestResponse(
        status="ok",
        provider=settings.llm_provider,
        model=settings.llm_model,
        answer=result.answer,
        cited_context_ids=result.cited_context_ids,
    )
