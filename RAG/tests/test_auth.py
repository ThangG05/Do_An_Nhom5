from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4
import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials
from app.api.dependencies import auth
from app.core.config import Settings
from app.models.enums import AccountStatus


@pytest.mark.asyncio
async def test_valid_jwt_resolves_active_user(monkeypatch) -> None:
    user_id = uuid4(); secret = "x" * 32
    settings = Settings(_env_file=None, auth_jwt_secret=secret)
    token = jwt.encode({"sub": str(user_id), "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=5), "iss": settings.auth_jwt_issuer,
        "aud": settings.auth_jwt_audience}, secret, algorithm="HS256")
    user = SimpleNamespace(id=user_id, status=AccountStatus.ACTIVE)
    session = SimpleNamespace(scalar=AsyncMock(return_value=user))
    monkeypatch.setattr(auth, "get_settings", lambda: settings)
    result = await auth.get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), session)
    assert result.id == user_id


@pytest.mark.asyncio
async def test_invalid_jwt_is_rejected(monkeypatch) -> None:
    monkeypatch.setattr(auth, "get_settings", lambda: Settings(_env_file=None, auth_jwt_secret="x" * 32))
    with pytest.raises(Exception) as error:
        await auth.get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid"),
                                    SimpleNamespace(scalar=AsyncMock()))
    assert error.value.status_code == 401
