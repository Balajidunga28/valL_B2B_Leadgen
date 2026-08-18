"""
url: /backend/app/models/lead.py
About:
  Lead entity representing a validated, potentially scored prospect.
  Links to a company and the raw record from which it was derived.
  Validation status and enrichment status track pipeline progress.
  Lead score is populated by Slice 7 scoring — not fabricated in Slice 1.
"""

import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Lead(BaseModel):
    """Validated lead record. Scoped to an organization."""
    __tablename__ = "leads"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )
    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_runs.id"),
        nullable=False,
        index=True,
    )
    raw_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_records.id"),
        nullable=False,
    )
    validation_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    validation_issues: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    enrichment_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    lead_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    score_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    score_components: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    company = relationship("Company", back_populates="leads")
    pipeline_run = relationship("PipelineRun")
