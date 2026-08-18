"""
url: /backend/app/schemas/dashboard.py
About:
  Pydantic schemas for dashboard API. Defines response shapes for
  dashboard metrics and recent activity.
"""

from datetime import datetime
from pydantic import BaseModel


class RecentRun(BaseModel):
    id: str
    query_text: str
    status: str
    total_extracted: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    total_runs: int
    total_records: int
    total_companies: int
    recent_runs: list[RecentRun]
