"""
url: /backend/app/config.py
About:
  Application configuration using pydantic-settings. Reads environment
  variables and provides typed configuration for database, auth, API keys,
  and external service settings. All secrets come from environment variables.
"""

import json
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ValLG"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@127.0.0.1:5432/vallg"
    DATABASE_URL_ASYNC: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/vallg"

    # Auth
    JWT_SECRET: str = "CHANGE-ME-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24  # 24 hours

    # Google Places API
    GOOGLE_PLACES_API_KEY: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


def get_cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "")
    if not raw:
        return ["http://localhost:5173", "http://localhost:3000"]
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    return [o.strip() for o in raw.split(",") if o.strip()]


settings = Settings()
