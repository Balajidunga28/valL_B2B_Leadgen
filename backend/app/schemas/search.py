"""
url: /backend/app/schemas/search.py
About:
  Pydantic schemas for search and pipeline API. Defines request/response
  shapes for search queries, pipeline runs, and raw record results.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    location: str | None = Field(None, max_length=255, description="Location filter")
    sources: list[str] = Field(
        default=["google_search", "openstreetmap", "web_search", "indiamart", "justdial"],
        description="Data sources to search",
    )
    limit: int = Field(default=100, ge=1, le=200, description="Max results per source")


class PipelineRunResponse(BaseModel):
    id: str
    query_text: str
    status: str
    sources_used: list[str]
    total_extracted: int | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RawRecordResponse(BaseModel):
    id: str
    source_adapter: str
    source_record_id: str | None = None
    raw_data: dict
    status: str
    retrieved_at: datetime

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    pipeline_run: PipelineRunResponse
    records: list[RawRecordResponse]
    total_count: int
