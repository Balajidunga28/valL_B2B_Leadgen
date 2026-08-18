"""
url: /backend/app/schemas/leads.py
About:
  Pydantic schemas for the unified Leads API. Combines company, enrichment,
  validation, and score data into a single response shape for the frontend.
"""

from datetime import datetime
from pydantic import BaseModel


class LeadResponse(BaseModel):
    id: str
    name: str
    industry: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    phone: str | None = None
    website: str | None = None
    rating: float | None = None
    review_count: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    source: str | None = None
    validation_status: str | None = None
    enrichment_description: str | None = None
    enrichment_email: str | None = None
    enrichment_social_links: dict | None = None
    total_score: float | None = None
    score_version: str | None = None
    scored_at: datetime | None = None

    model_config = {"from_attributes": True}
