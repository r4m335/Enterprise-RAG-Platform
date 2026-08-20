import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise RAG Platform"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://erag_user:erag_password@postgres:5432/erag_db"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://erag_test:erag_test@postgres_test:5432/erag_test_db"
    
    # Redis Settings
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Qdrant Settings
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "documents"
    
    # Storage Settings
    STORAGE_PATH: str = "/app/storage"
    STORAGE_PROVIDER: str = "LOCAL"

    # JWT Settings
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY_CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # LLM Settings (OpenAI / OpenRouter)
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 1000
    CHAT_HISTORY_MESSAGES: int = 5
    
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    RERANKER_MODEL: str = "BAAI/bge-reranker-large"
    
    # Need absolute paths for dotenv to be reliable from anywhere
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()
