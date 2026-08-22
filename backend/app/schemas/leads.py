"""
url: /backend/app/schemas/leads.py
About:
  Pydantic schemas for the unified Leads API. Combines company, enrichment,
  validation, and score data into a single response shape for the frontend.
"""

from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


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
    sources: list[str] = []
    validation_status: str | None = None
    enrichment_description: str | None = None
    enrichment_email: str | None = None
    enrichment_social_links: dict | None = None
    total_score: float | None = None
    score_version: str | None = None
    scored_at: datetime | None = None
    is_saved: bool = False

    model_config = {"from_attributes": True}


class LeadCreateRequest(BaseModel):
    company_id: UUID
    pipeline_run_id: UUID
    raw_record_id: UUID | None = None


class LeadCreateResponse(BaseModel):
    id: str
    company_id: str
    pipeline_run_id: str
    raw_record_id: str
    validation_status: str
    enrichment_status: str
    lead_score: float | None = None
    score_version: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
