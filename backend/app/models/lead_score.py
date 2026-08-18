"""
url: /backend/app/models/lead_score.py
About:
  Level 6 lead score for a company. Stores the total score and individual
  factor scores. Each score is traceable to its company and versioned
  so rule changes produce distinguishable results. Idempotent — re-running
  Level 6 replaces previous scores for the company.
"""

import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class LeadScore(BaseModel):
    """Level 6 lead score for a company. Scoped to an organization."""
    __tablename__ = "lead_scores"
    __table_args__ = (
        Index("ix_lead_scores_org", "organization_id"),
        Index("ix_lead_scores_company", "company_id"),
        Index("ix_lead_scores_total", "organization_id", "total_score"),
    )

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

    # Individual factor scores (0.0 - 1.0)
    industry_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    size_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    location_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    technology_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    data_quality_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    validation_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)

    # Total score (0 - 100)
    total_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # Scoring metadata
    score_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    scoring_formula: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scored_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    company = relationship("Company", back_populates="scores")
