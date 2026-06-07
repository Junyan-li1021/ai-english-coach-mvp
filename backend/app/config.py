"""
Speakeasy Backend — environment configuration via pydantic-settings.
"""

from __future__ import annotations

import json
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve the project root so that .env is always found relative to the repo.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # speakeasy/.env


class Settings(BaseSettings):
    """All runtime configuration read from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    MAX_TURNS: int = 10
    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:5173"]'

    # ── Aliyun NLS (ASR & TTS) ──────────────────────────────
    ALIYUN_ACCESS_KEY_ID: str = ""
    ALIYUN_ACCESS_KEY_SECRET: str = ""
    ALIYUN_NLS_APPKEY: str = ""

    # ── DeepSeek (LLM) ──────────────────────────────────────
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # ── Youdao (Oral Evaluation) ────────────────────────────
    YOUDAO_APP_KEY: str = ""
    YOUDAO_APP_SECRET: str = ""

    # ── Derived helpers ─────────────────────────────────────
    @property
    def cors_origins_list(self) -> list[str]:
        try:
            return json.loads(self.CORS_ORIGINS)
        except json.JSONDecodeError:
            return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton used across the app."""
    return Settings()
