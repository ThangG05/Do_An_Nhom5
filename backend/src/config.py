import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ENV_FILE = Path(os.environ.get("HVNH_ENV_FILE", _BACKEND_DIR / ".env"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = ""
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    JWT_SECRET_KEY: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REGISTRATION_TOKEN_EXPIRE_MINUTES: int = 10
    OTP_EXPIRE_MINUTES: int = 10
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    ALLOWED_EMAIL_DOMAIN: str = "hvnh.edu.vn"
    CORS_ORIGINS: str = "http://localhost:3000"
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "HVNH Hub <onboarding@resend.dev>"
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PRESIGNED_URL_EXPIRE: int = 900
    MAX_AVATAR_BYTES: int = 5 * 1024 * 1024
    MAX_SHORT_VIDEO_BYTES: int = 100 * 1024 * 1024
    MAX_AUDIO_BYTES: int = 25 * 1024 * 1024
    MAX_FILE_BYTES: int = 25 * 1024 * 1024
    LOGIN_MAX_FAILED_ATTEMPTS: int = 5
    LOGIN_LOCK_MINUTES: int = 15
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_LOGIN: int = 10
    RATE_LIMIT_OTP: int = 5
    RATE_LIMIT_RESET: int = 5
    RATE_LIMIT_REPORT: int = 10
    RATE_LIMIT_UPLOAD: int = 30
    RATE_LIMIT_CONTENT: int = 40
    AUTH_COOKIE_SECURE: bool = False
    AUTH_COOKIE_DOMAIN: str = ""
    RAG_SERVICE_TIMEOUT_SECONDS: float = 120.0
    RAG_CRAWLER_BACKGROUND_ENABLED: bool = True
    RAG_CRAWLER_RESTART_DELAY_SECONDS: float = 5.0
    REDIS_URL: str = ""
    REALTIME_REDIS_URL: str = ""
    REALTIME_REDIS_PREFIX: str = "hvnh:realtime"
    REALTIME_REDIS_CONNECT_TIMEOUT_SECONDS: float = 1.0
    REALTIME_REDIS_SOCKET_TIMEOUT_SECONDS: float = 5.0
    REALTIME_PRESENCE_TTL_SECONDS: int = 60
    REALTIME_PRESENCE_REFRESH_SECONDS: int = 20
    WEBSOCKET_TICKET_EXPIRE_SECONDS: int = 30

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
