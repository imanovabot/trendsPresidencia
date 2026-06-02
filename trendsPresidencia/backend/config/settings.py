"""Configuración de la aplicación"""
from __future__ import annotations

import os
from datetime import timedelta
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación desde variables de entorno"""

    # API Keys
    youtube_api_key: Optional[str] = Field(None, env="YOUTUBE_API_KEY")
    huggingface_api_key: Optional[str] = Field(None, env="HUGGINGFACE_API_KEY")

    # Nuevas redes
    tiktok_api_key: Optional[str] = Field(None, env="TIKTOK_API_KEY")
    x_bearer_token: Optional[str] = Field(None, env="X_BEARER_TOKEN")
    instagram_access_token: Optional[str] = Field(None, env="INSTAGRAM_ACCESS_TOKEN")

    # pytrends
    pytrends_language: str = Field("es-CO", env="PYTRENDS_LANGUAGE")
    pytrends_region: str = Field("CO", env="PYTRENDS_REGION")

    # News
    news_update_interval_minutes: int = Field(30, env="NEWS_UPDATE_INTERVAL_MINUTES")

    # Cache
    cache_ttl_seconds: int = Field(21600, env="CACHE_TTL_SECONDS")  # 6 horas

    # Auto Refresh
    auto_refresh_enabled: bool = Field(True, env="AUTO_REFRESH_ENABLED")
    auto_refresh_interval_minutes: int = Field(360, env="AUTO_REFRESH_INTERVAL_MINUTES")  # 6 horas

    # API
    api_v1_str: str = Field("/api/v1", env="API_V1_STR")
    project_name: str = Field("trendsPresidencia API", env="PROJECT_NAME")

    # CORS
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:8081", "http://187.77.14.245:8081", "*"]
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
