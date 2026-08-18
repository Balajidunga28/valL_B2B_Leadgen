"""
url: /backend/app/schemas/level3.py
About:
  Pydantic schemas for Level 3 CLEAN API. Defines request/response
  shapes for the cleaning pipeline endpoint.
"""

from pydantic import BaseModel, Field


class CleanRequest(BaseModel):
    pipeline_run_id: str | None = Field(
        None,
        description="Optional pipeline_run_id to clean only records from a specific run. "
                    "If None, all raw_records for the organization are cleaned.",
    )


class CleanResponse(BaseModel):
    raw_records_read: int
    raw_records_processed: int
    companies_created: int
    duplicates_identified: int
    clusters_with_multiple: int
    clusters_single: int
    records_with_changes: int
    records_without_changes: int
    raw_records_untouched: int
