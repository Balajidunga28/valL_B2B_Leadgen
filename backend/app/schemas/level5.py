"""
url: /backend/app/schemas/level5.py
About:
  Pydantic schemas for Level 5 ENRICH API.
"""

from datetime import datetime
from pydantic import BaseModel


class EnrichResponse(BaseModel):
    companies_read: int
    enriched: int
    with_website_scrape: int
    with_industry_inference: int
    with_metadata_extraction: int
    with_social_links: int
    with_email: int
    with_founded_year: int
    with_company_size: int
    with_description: int
    errors: int


class CompanyEnrichmentResponse(BaseModel):
    company_id: str
    company_name: str
    industry: str | None = None
    industry_source: str | None = None
    company_size: str | None = None
    founded_year: str | None = None
    description: str | None = None
    social_links: dict | None = None
    email: str | None = None
    additional_phones: list | None = None
    enriched_at: datetime | None = None

    model_config = {"from_attributes": True}
