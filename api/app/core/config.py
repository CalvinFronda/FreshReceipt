# api/app/core/config.py
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App Config
    PROJECT_NAME: str = "FreshReceipt API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str

    # OCR & AI (optional for now)
    VERYFI_CLIENT_ID: str | None = None
    VERYFI_CLIENT_SECRET: str | None = None
    VERYFI_USERNAME: str | None = None
    VERYFI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    # Rate limiting
    RATE_LIMIT_RECEIPTS_PER_DAY: int = 10

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8081",  # Expo local
        "exp://localhost:8081",
    ]

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True
        # Allow extra fields without error
        extra = "ignore"


settings = Settings()
