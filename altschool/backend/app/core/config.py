"""Конфигурация приложения."""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    APP_NAME: str = "AltSchool"
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"

    # Database
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/altschool"
    )

    # Auth
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # AI
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    DEFAULT_MODEL: str = os.environ.get("DEFAULT_MODEL", "gpt-4o-mini")

    # CORS
    CORS_ORIGINS: list[str] = None

    def __post_init__(self):
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set")
        if self.CORS_ORIGINS is None:
            origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
            self.CORS_ORIGINS = [o.strip() for o in origins.split(",")]


settings = Settings()
