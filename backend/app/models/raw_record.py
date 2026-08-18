"""
url: /backend/app/models/raw_record.py
About:
  Raw record entity storing unprocessed data from each source adapter.
  The raw_data JSONB field preserves the complete source response for
  provenance and reprocessing. This record is never deleted — it is
  the audit trail for the pipeline.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class RawRecord(BaseModel):
    """Raw extracted record from a source. Preserves original source data."""
    __tablename__ = "raw_records"
    __table_args__ = (
        Index("ix_raw_records_org_pipeline", "organization_id", "pipeline_run_id"),
        Index("ix_raw_records_org_source", "organization_id", "source_adapter"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_runs.id"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=True,
        index=True,
    )
    source_adapter: Mapped[str] = mapped_column(String(100), nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalized_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="extracted"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    pipeline_run = relationship("PipelineRun", back_populates="raw_records")
    company = relationship("Company", back_populates="raw_records")
