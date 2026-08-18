"""
url: /backend/app/schemas/settings.py
About:
  Pydantic schemas for settings API. Defines request/response shapes for
  API key management.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ApiKeyCreateRequest(BaseModel):
    source_adapter: str = Field(..., description="Source adapter name (e.g., google_places)")
    api_key: str = Field(..., min_length=1, description="API key value")


class ApiKeyResponse(BaseModel):
    id: str
    source_adapter: str
    api_key_hint: str
    status: str
    last_verified_at: datetime | None = None
    quota_used: int | None = None
    quota_limit: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyListResponse(BaseModel):
    keys: list[ApiKeyResponse]


class ApiKeyDeleteResponse(BaseModel):
    success: bool
    message: str
