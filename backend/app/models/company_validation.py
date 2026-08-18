"""
url: /backend/app/models/company_validation.py
About:
  Level 4 validation results for a company. Stores per-field validation
  status (email, phone, website, business existence) and overall status.
  Each record is traceable to exactly one company. Idempotent —
  re-running Level 4 replaces previous validation for the company.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CompanyValidation(BaseModel):
    """Level 4 validation result for a company. Scoped to an organization."""
    __tablename__ = "company_validations"
    __table_args__ = (
        Index("ix_company_validations_org", "organization_id"),
        Index("ix_company_validations_company", "company_id"),
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

    # Per-field validation status: VALID, INVALID, UNKNOWN, NOT_AVAILABLE
    email_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="NOT_AVAILABLE"
    )
    phone_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="NOT_AVAILABLE"
    )
    website_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="NOT_AVAILABLE"
    )
    business_existence_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UNKNOWN"
    )

    # Overall validation status
    overall_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )

    # Detailed validation results and errors
    validation_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validation_errors: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    company = relationship("Company", back_populates="validations")
