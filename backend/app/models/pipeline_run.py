"""
url: /backend/app/models/pipeline_run.py
About:
  Pipeline run entity tracking a search/extraction session. Records the
  query parameters, sources used, and counts at each pipeline stage.
  Used for audit trail and dashboard metrics.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PipelineRun(BaseModel):
    """A search/extraction pipeline run. Scoped to an organization."""
    __tablename__ = "pipeline_runs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="queued"
    )
    sources_used: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    total_extracted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_cleaned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_deduplicated: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_valid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_enriched: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="pipeline_runs")
    raw_records = relationship("RawRecord", back_populates="pipeline_run", lazy="selectin")
