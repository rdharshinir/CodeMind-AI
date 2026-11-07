"""Configuration loader for CodeMind AI."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable fallback and .env support."""

    # Hindsight Memory Configuration
    hindsight_api_key: Optional[str] = None
    hindsight_base_url: str = "https://api.hindsight.vectorize.io"
    hindsight_bank_id: str = "codemind-main-bank"

    # LLM Provider Configuration
    groq_api_key: Optional[str] = None
    groq_model: str = "qwen/qwen3.8-27b"

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    gemini_api_key: Optional[str] = None

    # Server Configuration
    codemind_host: str = "127.0.0.1"
    codemind_port: int = 8000
    codemind_debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    """Retrieve application settings instance."""
    return Settings()
