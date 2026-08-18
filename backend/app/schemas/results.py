"""
url: /backend/app/schemas/results.py
About:
  Pydantic schemas for results API. Defines request/response shapes for
  raw record listing, filtering, and detail views.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class RawRecordDetailResponse(BaseModel):
    id: str
    source_adapter: str
    source_record_id: str | None = None
    raw_data: dict
    normalized_data: dict | None = None
    status: str
    error_message: str | None = None
    retrieved_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class RawRecordListResponse(BaseModel):
    records: list[RawRecordDetailResponse]
    total_count: int
    page: int
    page_size: int


class PipelineRunDetailResponse(BaseModel):
    id: str
    query_text: str
    query_params: dict
    status: str
    sources_used: list[str]
    total_extracted: int | None = None
    total_cleaned: int | None = None
    total_deduplicated: int | None = None
    total_valid: int | None = None
    total_enriched: int | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PipelineRunListResponse(BaseModel):
    runs: list[PipelineRunDetailResponse]
    total_count: int
