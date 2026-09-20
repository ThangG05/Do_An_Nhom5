from functools import lru_cache
import os
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SHARED_ENV_FILE = Path(os.environ.get("HVNH_ENV_FILE", _PROJECT_ROOT / "backend" / ".env"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_SHARED_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "HVNH RAG AI Service"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    docs_enabled: bool = True
    log_level: str = "INFO"
    log_json: bool = True
    internal_api_key: str | None = None
    cors_allowed_origins: list[str] = Field(default_factory=list)
    trusted_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )
    max_request_body_bytes: int = Field(default=64 * 1024, ge=1024, le=10 * 1024 * 1024)
    postgres_user: str = "hvnh"
    postgres_password: str = "change-me"
    postgres_db: str = "hvnh_rag"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str | None = None
    db_echo: bool = False
    db_pool_size: int = Field(default=10, ge=1)
    db_max_overflow: int = Field(default=20, ge=0)
    db_pool_recycle_seconds: int = Field(default=300, ge=30, le=3600)
    db_command_timeout_seconds: float = Field(default=30, gt=0, le=300)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_api_key: str | None = None
    qdrant_collection: str = "hvnh_documents"
    qdrant_https: bool = False
    qdrant_timeout_seconds: float = Field(default=30, gt=0)
    qdrant_max_retries: int = Field(default=2, ge=0, le=5)
    qdrant_retry_base_seconds: float = Field(default=0.5, ge=0.1, le=10)
    embedding_provider: str = "modal"
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimensions: int = Field(default=1024, ge=128, le=3072)
    embedding_batch_size: int = Field(default=20, ge=1, le=100)
    modal_embedding_app: str = "hvnh_rag"
    modal_embedding_class: str = "BgeM3"
    embedding_timeout_seconds: int = Field(default=600, ge=10, le=1800)
    embedding_max_retries: int = Field(default=4, ge=0, le=8)
    embedding_retry_base_seconds: float = Field(default=2.0, ge=0.1, le=30)
    ocr_provider: str = "modal"
    modal_ocr_app: str = "hvnh_rag"
    modal_ocr_class: str = "PdfOCR"
    ocr_timeout_seconds: int = Field(default=900, ge=30, le=3600)
    ocr_max_retries: int = Field(default=2, ge=0, le=5)
    ocr_max_pages: int = Field(default=80, ge=1, le=1000)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    retrieval_candidate_k: int = Field(default=20, ge=5, le=100)
    retrieval_hybrid_enabled: bool = True
    retrieval_reranker: str = "heuristic"
    retrieval_lexical_candidate_k: int = Field(default=20, ge=5, le=100)
    retrieval_candidate_score_threshold: float = Field(default=0.30, ge=0, le=1)
    retrieval_score_threshold: float = Field(default=0.45, ge=0, le=1)
    retrieval_max_chunks_per_document: int = Field(default=2, ge=1, le=10)
    conversation_recent_messages: int = Field(default=8, ge=2, le=20)
    conversation_summary_trigger_messages: int = Field(default=12, ge=4, le=100)
    conversation_summary_max_chars: int = Field(default=4000, ge=500, le=20000)
    auth_jwt_secret: SecretStr | None = None
    auth_jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    auth_jwt_issuer: str = "hvnh-hub"
    auth_jwt_audience: str = "hvnh-rag-api"
    auth_service_url: str | None = None
    auth_service_timeout_seconds: float = Field(default=8, gt=0, le=30)
    rag_rate_limit_per_minute: int = Field(default=10, ge=1, le=1000)
    rag_global_concurrency: int = Field(default=10, ge=1, le=100)
    rag_concurrency_lease_seconds: int = Field(default=180, ge=30, le=1800)
    rag_contract_max_attempts: int = Field(default=3, ge=1, le=5)
    chunk_size_chars: int = Field(default=1800, ge=500, le=10000)
    chunk_overlap_chars: int = Field(default=250, ge=0, le=2000)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    redis_ssl: bool = False
    redis_url: str | None = None
    redis_timeout_seconds: float = Field(default=5, gt=0)
    crawler_stream: str = "hvnh:crawl:runs"
    crawler_consumer_group: str = "hvnh-crawler-workers"
    crawler_consumer_name: str = "worker-1"
    pipeline_stream: str = "hvnh:pipeline:runs"
    pipeline_consumer_group: str = "hvnh-pipeline-workers"
    pipeline_consumer_name: str = "pipeline-worker-1"
    pipeline_lock_seconds: int = Field(default=3600, ge=60, le=86400)
    pipeline_stage_timeout_seconds: int = Field(default=7200, ge=60, le=14400)
    pipeline_max_retries: int = Field(default=3, ge=0, le=10)
    pipeline_retry_base_seconds: float = Field(default=5.0, ge=0.1, le=300)
    crawler_scheduler_poll_seconds: int = Field(default=30, ge=5, le=3600)
    crawler_queue_block_ms: int = Field(default=5000, ge=100, le=60000)
    crawler_lock_seconds: int = Field(default=3600, ge=60, le=86400)
    crawler_run_stale_minutes: int = Field(default=120, ge=15, le=10080)
    crawler_recovery_retry_minutes: int = Field(default=5, ge=1, le=1440)
    crawler_recovery_max_attempts: int = Field(default=3, ge=0, le=20)
    crawler_http_timeout_seconds: float = Field(default=30, gt=0, le=120)
    crawler_max_response_bytes: int = Field(default=25 * 1024 * 1024, ge=1024, le=100 * 1024 * 1024)
    crawler_max_redirects: int = Field(default=3, ge=0, le=10)
    crawler_user_agent: str = "HVNH-RAG-Crawler/1.0 (+https://hvnh.edu.vn)"
    llm_provider: str = "gemini"
    llm_model: str = "gemini-3.5-flash-lite"
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_temperature: float = Field(default=0.1, ge=0, le=2)
    llm_timeout_seconds: int = Field(default=60, ge=1)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    llm_retry_base_seconds: float = Field(default=1.0, ge=0.1, le=10)
    llm_max_input_chars: int = Field(default=4000, ge=100, le=50000)
    llm_max_output_tokens: int = Field(default=1024, ge=64, le=8192)
    llm_max_context_chars: int = Field(default=30000, ge=1000, le=200000)
    ragas_judge_provider: str | None = None
    ragas_judge_model: str | None = None
    ragas_judge_api_key: str | None = None
    ragas_judge_base_url: str | None = None

    @model_validator(mode="after")
    def validate_production_boundaries(self) -> "Settings":
        if self.environment.casefold() not in {"production", "prod"}:
            return self
        secret = self.auth_jwt_secret.get_secret_value() if self.auth_jwt_secret else ""
        if len(secret) < 32:
            raise ValueError("AUTH_JWT_SECRET must contain at least 32 characters in production")
        if self.docs_enabled:
            raise ValueError("DOCS_ENABLED must be false in production")
        if not self.cors_allowed_origins or "*" in self.cors_allowed_origins:
            raise ValueError("CORS_ALLOWED_ORIGINS must explicitly list the production frontend")
        if not self.trusted_hosts or "*" in self.trusted_hosts:
            raise ValueError("TRUSTED_HOSTS must explicitly list production hostnames")
        for origin in self.cors_allowed_origins:
            parts = urlsplit(origin)
            if parts.scheme != "https" or not parts.hostname or parts.path not in {"", "/"} \
                    or parts.query or parts.fragment or parts.username or parts.password:
                raise ValueError("production CORS origins must be HTTPS origins without paths")
        if any("://" in host or "/" in host for host in self.trusted_hosts):
            raise ValueError("TRUSTED_HOSTS entries must be hostnames, not URLs")
        return self

    @property
    def sqlalchemy_database_uri(self) -> str:
        url = self.database_url or (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url.removeprefix("postgres://")
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url.removeprefix("postgresql://")

        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        ssl_mode = query.pop("sslmode", None)
        query.pop("channel_binding", None)
        if ssl_mode and "ssl" not in query:
            query["ssl"] = ssl_mode
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    @property
    def qdrant_connection_url(self) -> str:
        if self.qdrant_host.startswith(("http://", "https://")):
            return self.qdrant_host.rstrip("/")
        scheme = "https" if self.qdrant_https else "http"
        return f"{scheme}://{self.qdrant_host}:{self.qdrant_port}"

    @property
    def redis_connection_uri(self) -> str:
        if self.redis_url:
            return self.redis_url
        raw_host = self.redis_host.strip()
        parsed = urlsplit(raw_host if "://" in raw_host else f"//{raw_host}")
        host = parsed.hostname or raw_host
        port = parsed.port or self.redis_port
        scheme = "rediss" if self.redis_ssl or parsed.scheme in {"https", "rediss"} else "redis"
        password = quote(self.redis_password, safe="") if self.redis_password else ""
        credentials = f":{password}@" if password else ""
        return f"{scheme}://{credentials}{host}:{port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
