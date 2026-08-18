"""
url: /backend/app/models/company.py
About:
  Company entity representing a deduplicated business record. Companies
  are created from raw records and linked via source_place_id (Google Places)
  or source_cin (MCA). Fields are limited to what approved sources actually provide.
"""

import uuid
from decimal import Decimal

from sqlalchemy import String, Text, Numeric, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Company(BaseModel):
    """Deduplicated company record. Scoped to an organization."""
    __tablename__ = "companies"
    __table_args__ = (
        Index("ix_companies_org_domain", "organization_id", "domain"),
        Index("ix_companies_org_place_id", "organization_id", "source_place_id"),
        Index("ix_companies_org_cin", "organization_id", "source_cin"),
        Index("ix_companies_org_name", "organization_id", "name"),
        Index("ix_companies_city_state", "city", "state"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    categories: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone_intl: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1), nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    business_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    google_maps_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_place_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_cin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    completeness_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="companies")
    raw_records = relationship("RawRecord", back_populates="company", lazy="selectin")
    leads = relationship("Lead", back_populates="company", lazy="selectin")
    validations = relationship("CompanyValidation", back_populates="company", lazy="selectin")
    enrichments = relationship("CompanyEnrichment", back_populates="company", lazy="selectin")
    scores = relationship("LeadScore", back_populates="company", lazy="selectin")
