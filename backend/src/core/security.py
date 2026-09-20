import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from src.config import settings

password_hash = PasswordHash.recommended()


def create_access_token(user_id: str) -> tuple[str, int]:
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_in


def create_refresh_token() -> tuple[str, str, datetime]:
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return token, token_hash, expires_at


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except InvalidTokenError as exc:
        raise ValueError("Access token không hợp lệ hoặc đã hết hạn.") from exc
    if payload.get("type") != "access" or not payload.get("sub"):
        raise ValueError("Access token không hợp lệ.")
    return str(payload["sub"])


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    if encoded_hash.startswith("!"):
        return False
    return password_hash.verify(password, encoded_hash)


def hash_verification_code(user_id: str, code: str) -> str:
    message = f"{user_id}:{code}".encode("utf-8")
    return hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()


def verification_code_matches(user_id: str, code: str, expected_hash: str) -> bool:
    actual_hash = hash_verification_code(user_id, code)
    return hmac.compare_digest(actual_hash, expected_hash)


def create_registration_token(user_id: str) -> tuple[str, int]:
    expires_in = settings.REGISTRATION_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "type": "registration",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_in


def decode_registration_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except InvalidTokenError as exc:
        raise ValueError("Phiên xác thực đã hết hạn hoặc không hợp lệ.") from exc
    if payload.get("type") != "registration" or not payload.get("sub"):
        raise ValueError("Phiên xác thực không hợp lệ.")
    return str(payload["sub"])
