from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = ""
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

settings = Settings()
