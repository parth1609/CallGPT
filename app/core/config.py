import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App Config
    APP_TITLE: str = "CallGPT"
    APP_VERSION: str = "1.0.0"

    # Database (Postgres)
    DATABASE_URL: Optional[str] = None

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_API_KEY: Optional[str] = None  # Optional, for pgvector operations
    SUPABASE_BUCKET: str

    # Pinecone
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"

    # LLM & AI
    GROQ_API_KEY: str
    LLM_MODEL: str = "openai/gpt-oss-120b"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields like old SERVICE_URLs


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
