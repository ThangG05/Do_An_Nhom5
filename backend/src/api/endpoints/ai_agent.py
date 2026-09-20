from typing import Any, Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field

from src.api.dependencies import CurrentUser
from src.agents.rag_runtime import get_rag_app
from src.config import settings

router = APIRouter(prefix="/ai", tags=["AI Agent"])


class AIChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None


class AIConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=500)


class AIConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=500)


def _authorization(request: Request) -> str:
    value = request.headers.get("authorization", "")
    if not value.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bạn chưa đăng nhập.")
    return value


async def _forward(
    method: str,
    path: str,
    request: Request,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> httpx.Response:
    url = f"http://127.0.0.1/api/v1/{path.lstrip('/')}"
    try:
        transport = httpx.ASGITransport(app=get_rag_app())
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1",
            timeout=settings.RAG_SERVICE_TIMEOUT_SECONDS,
        ) as client:
            response = await client.request(
                method,
                url,
                headers={"Authorization": _authorization(request), "X-Request-ID": request.headers.get("x-request-id", "")},
                json=json,
                params=params,
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Trợ lý AI phản hồi quá thời gian.") from None
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Không thể kết nối dịch vụ trợ lý AI.") from None
    return response


def _payload(response: httpx.Response) -> Any:
    if response.status_code == 204:
        return None
    try:
        return response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Dịch vụ trợ lý AI trả về dữ liệu không hợp lệ.") from None


def _result(response: httpx.Response) -> Any:
    payload = _payload(response)
    if response.is_error:
        detail = payload.get("detail") if isinstance(payload, dict) else None
        messages = {
            400: "Câu hỏi không hợp lệ hoặc không đáp ứng chính sách an toàn.",
            401: "Phiên đăng nhập không hợp lệ.",
            404: "Không tìm thấy cuộc hội thoại.",
            429: "Bạn đang hỏi quá nhanh. Vui lòng thử lại sau.",
            503: "Trợ lý AI đang tạm thời bận hoặc chưa sẵn sàng.",
        }
        raise HTTPException(status_code=response.status_code, detail=messages.get(response.status_code, detail or "Không thể xử lý yêu cầu AI."))
    return payload


@router.get("/health", summary="Kiểm tra dịch vụ RAG")
async def ai_health(_: CurrentUser, request: Request) -> Any:
    return _result(await _forward("GET", "/health", request))


@router.post("/chat", summary="Hỏi trợ lý HVNH")
async def ai_chat(body: AIChatRequest, _: CurrentUser, request: Request) -> Any:
    return _result(await _forward("POST", "/rag/chat", request, json=body.model_dump(mode="json")))


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(body: AIConversationCreate, _: CurrentUser, request: Request) -> Any:
    return _result(await _forward("POST", "/conversations", request, json=body.model_dump(mode="json")))


@router.get("/conversations")
async def list_conversations(_: CurrentUser, request: Request,
                             limit: int = Query(default=30, ge=1, le=100),
                             offset: int = Query(default=0, ge=0)) -> Any:
    return _result(await _forward("GET", "/conversations", request, params={"limit": limit, "offset": offset}))


@router.get("/conversations/{conversation_id}/messages")
async def conversation_messages(conversation_id: UUID, _: CurrentUser, request: Request,
                                limit: int = Query(default=100, ge=1, le=500),
                                before_sequence: int | None = Query(default=None, ge=1)) -> Any:
    params: dict[str, Any] = {"limit": limit}
    if before_sequence is not None:
        params["before_sequence"] = before_sequence
    return _result(await _forward("GET", f"/conversations/{conversation_id}/messages", request, params=params))


@router.patch("/conversations/{conversation_id}")
async def rename_conversation(conversation_id: UUID, body: AIConversationUpdate,
                              _: CurrentUser, request: Request) -> Any:
    return _result(await _forward("PATCH", f"/conversations/{conversation_id}", request, json=body.model_dump()))


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: UUID, _: CurrentUser, request: Request) -> Response:
    upstream = await _forward("DELETE", f"/conversations/{conversation_id}", request)
    _result(upstream)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
