"""App configuration loaded from environment / .env file."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for runtime config."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"

    # Scraping
    maps_min_delay_sec: float = 5.0
    maps_max_delay_sec: float = 10.0
    website_concurrency: int = Field(default=5, ge=1)
    website_timeout_sec: int = Field(default=20, ge=1)
    default_phone_region: str = "US"
    headless: bool = True

    # Job retention
    max_jobs_in_memory: int = 200

    # Legacy SQLite + Google Sheets pipeline used by CLI/tests
    db_path: Path = Path("data/prospector.db")
    google_sheet_id: str | None = None
    google_worksheet_name: str = "Leads"
    google_creds_path: Path = Path("google-service-account.json")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
