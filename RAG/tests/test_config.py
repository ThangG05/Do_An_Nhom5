import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_neon_url_is_normalized_for_asyncpg() -> None:
    settings = Settings(
        database_url=(
            "postgresql://user:pass@example.neon.tech/db"
            "?sslmode=require&channel_binding=require"
        )
    )
    assert settings.sqlalchemy_database_uri == (
        "postgresql+asyncpg://user:pass@example.neon.tech/db?ssl=require"
    )


def test_cloud_service_urls_support_tls() -> None:
    settings = Settings(
        qdrant_host="cluster.example.com",
        qdrant_port=6333,
        qdrant_https=True,
        redis_host="redis.example.com",
        redis_port=6379,
        redis_password="p@ss",
        redis_ssl=True,
        redis_url=None,
    )
    assert settings.qdrant_connection_url == "https://cluster.example.com:6333"
    assert settings.redis_connection_uri == "rediss://:p%40ss@redis.example.com:6379/0"


def test_redis_host_accepts_upstash_https_endpoint() -> None:
    settings = Settings(
        redis_host="https://example.upstash.io",
        redis_port=6379,
        redis_password="secret",
        redis_ssl=True,
        redis_url=None,
    )
    assert settings.redis_connection_uri == "rediss://:secret@example.upstash.io:6379/0"


def test_production_rejects_open_or_incomplete_http_boundary() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production", docs_enabled=True,
                 auth_jwt_secret="short", cors_allowed_origins=["*"], trusted_hosts=["*"])


def test_production_accepts_explicit_http_boundary() -> None:
    settings = Settings(
        _env_file=None, environment="production", docs_enabled=False,
        auth_jwt_secret="x" * 32, cors_allowed_origins=["https://app.example.edu.vn"],
        trusted_hosts=["api.example.edu.vn"],
    )
    assert settings.trusted_hosts == ["api.example.edu.vn"]


def test_production_rejects_insecure_origin_and_url_shaped_host() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production", docs_enabled=False,
                 auth_jwt_secret="x" * 32,
                 cors_allowed_origins=["http://app.example.edu.vn/path"],
                 trusted_hosts=["https://api.example.edu.vn"])
