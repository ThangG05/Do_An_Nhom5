from uuid import UUID
import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.db.session import get_db
from app.models.auth import User
from app.models.enums import AccountStatus

bearer = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
                           session: AsyncSession = Depends(get_db)) -> User:
    settings = get_settings()
    local_secret = settings.auth_jwt_secret.get_secret_value() if settings.auth_jwt_secret else ""
    if not settings.auth_service_url and len(local_secret) < 32:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Public chat disabled")
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if settings.auth_service_url == "inprocess://backend":
        try:
            from src.core.security import decode_access_token

            user_id = UUID(decode_access_token(credentials.credentials))
        except (ImportError, ValueError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized") from None
    elif settings.auth_service_url:
        try:
            async with httpx.AsyncClient(timeout=settings.auth_service_timeout_seconds) as client:
                response = await client.get(settings.auth_service_url, headers={"Authorization": f"Bearer {credentials.credentials}"})
            if response.status_code != 200:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
            user_id = UUID(str(response.json()["id"]))
        except HTTPException:
            raise
        except (httpx.HTTPError, KeyError, ValueError, TypeError):
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service unavailable") from None
    else:
        try:
            payload = jwt.decode(credentials.credentials, local_secret,
                algorithms=[settings.auth_jwt_algorithm], audience=settings.auth_jwt_audience,
                issuer=settings.auth_jwt_issuer, options={"require": ["exp", "sub", "iat"]})
            user_id = UUID(str(payload["sub"]))
        except (InvalidTokenError, KeyError, ValueError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized") from None
    user = await session.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None),
                                                    User.status == AccountStatus.ACTIVE))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user
