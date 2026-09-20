from fastapi import APIRouter
from src.api.endpoints import auth, users, ai_agent, media, posts, notifications, chat, groups, admin, reports, system

router = APIRouter()

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(ai_agent.router)
router.include_router(media.router)
router.include_router(posts.router)
router.include_router(notifications.router)
router.include_router(chat.router)
router.include_router(groups.router)
router.include_router(admin.router)
router.include_router(reports.router)
router.include_router(system.router)
