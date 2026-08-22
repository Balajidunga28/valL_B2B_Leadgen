"""
url: /backend/app/schemas/search.py
About:
  Pydantic schemas for search and pipeline API. Defines request/response
  shapes for search queries, pipeline runs, and raw record results.
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# Ordered list of valid sources (order matters for default)
VALID_SOURCES_ORDERED = ["google_search", "google_maps_scraper", "openstreetmap", "web_search", "indiamart", "justdial"]
VALID_SOURCES = frozenset(VALID_SOURCES_ORDERED)
MAX_RESULTS_PER_SOURCE = 200
MIN_RESULTS_PER_SOURCE = 1


def validate_sources(v: list[str]) -> list[str]:
    """Validate and filter sources against known valid sources."""
    if not v:
        raise ValueError("At least one source must be specified")
    invalid = [s for s in v if s not in VALID_SOURCES]
    if invalid:
        raise ValueError(f"Invalid source(s): {', '.join(invalid)}. Valid sources: {', '.join(VALID_SOURCES_ORDERED)}")
    return list(dict.fromkeys(v))  # Remove duplicates, preserve order


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    location: str | None = Field(None, max_length=255, description="Location filter")
    sources: list[str] = Field(
        default=VALID_SOURCES_ORDERED,
        description="Data sources to search",
    )
    limit: int = Field(default=100, ge=MIN_RESULTS_PER_SOURCE, le=MAX_RESULTS_PER_SOURCE, description="Max results per source")

    @field_validator("sources", mode="before")
    @classmethod
    def _validate_sources(cls, v: list[str]) -> list[str]:
        return validate_sources(v)


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
