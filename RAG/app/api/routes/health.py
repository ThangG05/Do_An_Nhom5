import asyncio

from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.database import check_database
from app.services.qdrant import check_qdrant
from app.services.redis import check_redis

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Service liveness")
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Dependency readiness")
async def readiness(response: Response) -> ReadinessResponse:
    names = ("database", "qdrant", "redis")
    results = await asyncio.gather(
        check_database(), check_qdrant(), check_redis(), return_exceptions=True
    )
    checks = {
        name: "error" if isinstance(result, BaseException) else "ok"
        for name, result in zip(names, results, strict=True)
    }
    ready = all(value == "ok" for value in checks.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="ready" if ready else "not_ready", checks=checks)
