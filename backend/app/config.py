from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Sistem Input & Rekap Nilai"
    institution_name: str = ""
    debug: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/grades"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    superadmin_email: str = "admin@example.com"
    superadmin_password: str = ""
    superadmin_name: str = "Superadmin"
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_security: Literal["starttls", "ssl", "none"] = "starttls"
    smtp_timeout: float = Field(default=10, gt=0, le=60)

@lru_cache
def get_settings() -> Settings:
    return Settings()
