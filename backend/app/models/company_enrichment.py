"""
url: /backend/app/models/company_enrichment.py
About:
  Level 5 enrichment results for a company. Stores additional business
  information gathered from website scraping, name inference, and metadata
  extraction. Each field retains its source/provenance. Idempotent —
  re-running Level 5 replaces previous enrichment for the company.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CompanyEnrichment(BaseModel):
    """Level 5 enrichment result for a company. Scoped to an organization."""
    __tablename__ = "company_enrichments"
    __table_args__ = (
        Index("ix_company_enrichments_org", "organization_id"),
        Index("ix_company_enrichments_company", "company_id"),
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

    # Enrichment fields
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry_source: Mapped[str | None] = mapped_column(String(500), nullable=True)

    company_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_size_source: Mapped[str | None] = mapped_column(String(500), nullable=True)

    revenue_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    revenue_range_source: Mapped[str | None] = mapped_column(String(500), nullable=True)

    founded_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    founded_year_source: Mapped[str | None] = mapped_column(String(500), nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_source: Mapped[str | None] = mapped_column(String(500), nullable=True)

    social_links: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    social_links_source: Mapped[str | None] = mapped_column(String(500), nullable=True)

    technologies: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    technologies_source: Mapped[str | None] = mapped_column(String(500), nullable=True)

    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_source: Mapped[str | None] = mapped_column(String(500), nullable=True)

    additional_phones: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    additional_phones_source: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Raw enrichment data from all sources
    enrichment_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timestamps
    enriched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    company = relationship("Company", back_populates="enrichments")
