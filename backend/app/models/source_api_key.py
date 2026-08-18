"""
url: /backend/app/models/source_api_key.py
About:
  Source API key entity storing encrypted API keys per organization.
  Keys are encrypted at rest using AES-256. Only the last 4 characters
  are stored in plaintext for display purposes. All external API calls
  go through the backend — frontend never has access to raw API keys.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey,Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SourceApiKey(BaseModel):
    """Encrypted API key for an external source. Scoped to an organization."""
    __tablename__ = "source_api_keys"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    source_adapter: Mapped[str] = mapped_column(String(100), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_hint: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    quota_used: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    quota_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
