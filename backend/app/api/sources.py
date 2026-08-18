"""
url: /backend/app/api/sources.py
About:
  Sources API endpoints for ValLG. Provides real-time statistics about all
  data providers: candidates contributed, canonical leads, last run time,
  and current status. All data is computed from actual raw_records and
  pipeline_runs — no fabricated or cached statistics.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, distinct, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.pipeline_run import PipelineRun
from app.models.raw_record import RawRecord
from app.models.source_api_key import SourceApiKey
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/sources", tags=["sources"])

ALL_SOURCES = [
    {
        "adapter_name": "google_search",
        "display_name": "Google Maps",
        "category": "Search & Maps",
        "description": "Browser-based Google Maps scraping for business listings with reviews, ratings, and contact info.",
        "requires_api_key": False,
        "free": True,
    },
    {
        "adapter_name": "openstreetmap",
        "display_name": "OpenStreetMap",
        "category": "Search & Maps",
        "description": "Open data from OpenStreetMap Overpass API. Free, no API key required.",
        "requires_api_key": False,
        "free": True,
    },
    {
        "adapter_name": "web_search",
        "display_name": "Web Search (Bing)",
        "category": "Search & Maps",
        "description": "Discovers business listings through Bing search results and directory pages.",
        "requires_api_key": False,
        "free": True,
    },
    {
        "adapter_name": "google_places",
        "display_name": "Google Places API",
        "category": "Search & Maps",
        "description": "Google Places API (New) for structured business data with reviews and details.",
        "requires_api_key": True,
        "free": False,
    },
    {
        "adapter_name": "indiamart",
        "display_name": "IndiaMART",
        "category": "Business Directory",
        "description": "India's largest B2B marketplace directory. Scrapes product/service listings.",
        "requires_api_key": False,
        "free": True,
    },
    {
        "adapter_name": "justdial",
        "display_name": "JustDial",
        "category": "Business Directory",
        "description": "Local business directory for India. Provides phone numbers and addresses.",
        "requires_api_key": False,
        "free": True,
    },
]


@router.get("")
async def list_sources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all data providers with real-time statistics from the database."""
    org_id = current_user.organization_id

    source_stats = {}

    for source in ALL_SOURCES:
        adapter_name = source["adapter_name"]

        candidates_result = await db.execute(
            select(func.count()).select_from(RawRecord).where(
                RawRecord.organization_id == org_id,
                RawRecord.source_adapter == adapter_name,
            )
        )
        candidates_count = candidates_result.scalar() or 0

        contributing_result = await db.execute(
            select(func.count()).select_from(RawRecord).where(
                RawRecord.organization_id == org_id,
            ).where(
                text(f"raw_data->'metadata'->'contributing_sources' ? '{adapter_name}'")
            )
        )
        contributing_count = contributing_result.scalar() or 0

        last_run_result = await db.execute(
            select(PipelineRun.created_at)
            .where(
                PipelineRun.organization_id == org_id,
                PipelineRun.sources_used.any(adapter_name),
                PipelineRun.status == "completed",
            )
            .order_by(PipelineRun.created_at.desc())
            .limit(1)
        )
        last_run_row = last_run_result.first()
        last_run_at = last_run_row[0] if last_run_row else None

        total_runs_result = await db.execute(
            select(func.count()).select_from(PipelineRun).where(
                PipelineRun.organization_id == org_id,
                PipelineRun.sources_used.any(adapter_name),
            )
        )
        total_runs = total_runs_result.scalar() or 0

        has_api_key = False
        if source["requires_api_key"]:
            key_result = await db.execute(
                select(SourceApiKey).where(
                    SourceApiKey.organization_id == org_id,
                    SourceApiKey.source_adapter == adapter_name,
                    SourceApiKey.status == "active",
                )
            )
            has_api_key = key_result.scalar_one_or_none() is not None

        if source["requires_api_key"] and not has_api_key:
            status = "not_configured"
        elif candidates_count == 0 and total_runs == 0:
            status = "available"
        elif candidates_count > 0:
            status = "active"
        else:
            status = "available"

        source_stats[adapter_name] = {
            "adapter_name": adapter_name,
            "display_name": source["display_name"],
            "category": source["category"],
            "description": source["description"],
            "requires_api_key": source["requires_api_key"],
            "free": source["free"],
            "status": status,
            "candidates_contributed": candidates_count,
            "leads_enriched": contributing_count,
            "total_runs": total_runs,
            "last_run_at": last_run_at.isoformat() if last_run_at else None,
            "has_api_key": has_api_key,
        }

    return {"sources": list(source_stats.values())}
