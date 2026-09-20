import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://hvnh:change-me@localhost:5432/hvnh_rag_test")
os.environ.setdefault("LOG_JSON", "false")
