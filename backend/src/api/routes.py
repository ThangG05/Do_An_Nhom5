from fastapi import APIRouter
from src.api.endpoints import auth, users, ai_agent

router = APIRouter()

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(ai_agent.router)
