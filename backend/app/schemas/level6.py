"""
url: /backend/app/schemas/level6.py
About:
  Pydantic schemas for Level 6 SCORE/Filter API.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class ScoreResponse(BaseModel):
    companies_read: int
    scored: int
    high: int
    medium: int
    low: int
    min_score: float
    max_score: float
    avg_score: float


class LeadScoreResponse(BaseModel):
    company_id: str
    company_name: str
    industry_score: float
    size_score: float
    location_score: float
    technology_score: float
    data_quality_score: float
    validation_score: float
    total_score: float
    score_version: str
    scored_at: datetime | None = None

    model_config = {"from_attributes": True}


class FilterRequest(BaseModel):
    min_score: float | None = None
    max_score: float | None = None
    industry: str | None = None
    has_phone: bool | None = None
    has_email: bool | None = None
    has_website: bool | None = None
    validation_status: str | None = None
    city: str | None = None
