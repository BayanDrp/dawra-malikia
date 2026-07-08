from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "الدورة العلمية الأولى في الفقه المالكي"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    SECRET_KEY: str = "change-me-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite:///./data/app.db"

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str | None = None
    SMTP_USE_TLS: bool = True

    ADMIN_EMAIL: str | None = None
    SITE_URL: str = "http://localhost:8000"

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    CORS_ORIGINS: list[str] = ["*"]

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS == ["*"] or self.CORS_ORIGINS == "*":
            return ["*"]
        if isinstance(self.CORS_ORIGINS, str):
            return [o.strip() for o in self.CORS_ORIGINS.split(",")]
        return list(self.CORS_ORIGINS)

    DATABASE_DIR: Path = Path("data")
    LOG_DIR: Path = Path("logs")

    def model_post_init(self, __context):
        self.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

        if self.SECRET_KEY == "change-me-to-a-random-secret-key" and self.DEBUG:
            import secrets
            self.SECRET_KEY = secrets.token_hex(32)


settings = Settings()
