from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.internal_llm import router as internal_llm_router
from app.api.routes.internal_rag import router as internal_rag_router
from app.api.routes.rag import router as rag_router
from app.api.routes.conversations import router as conversations_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(internal_llm_router, tags=["internal"])
api_router.include_router(internal_rag_router, tags=["internal"])
api_router.include_router(rag_router, tags=["rag"])
api_router.include_router(conversations_router, tags=["conversations"])
