import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Paavai Smart Campus AI Application Configuration.
    Loads from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core Application Settings
    APP_NAME: str = "Paavai Smart Campus AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/smartcampus.db"
    SYNC_DATABASE_URL: str = "sqlite:///./data/smartcampus.db"

    # Security & JWT Authentication
    JWT_SECRET: str = "paavai-smart-campus-ai-super-secret-key-change-in-production-2025"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Hugging Face Transformer Models
    HF_TOKEN: str = ""
    HF_INTENT_MODEL: str = "distilbert/distilbert-base-uncased"
    HF_GRIEVANCE_MODEL: str = "distilbert/distilbert-base-uncased"
    HF_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CLASSIFIER_CONFIDENCE_THRESHOLD: float = 0.75

    # Ollama Local LLM Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_TIMEOUT_SECONDS: int = 45

    # RAG Vector Retrieval Parameters
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.60
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 80
    VECTOR_STORE_DIR: str = "./data/faiss_index"
    UPLOAD_DOCUMENTS_DIR: str = "./data/documents"

    # CORS Settings
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()
