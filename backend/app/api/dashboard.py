"""
url: /backend/app/api/dashboard.py
About:
  Dashboard API endpoints for ValLG. Provides aggregated metrics and
  recent activity for the organization dashboard. All data is real —
  computed from actual pipeline runs and raw records.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.pipeline_run import PipelineRun
from app.models.raw_record import RawRecord
from app.models.company import Company
from app.api.deps import get_current_user
from app.schemas.dashboard import DashboardResponse, RecentRun

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard metrics and recent activity for the organization."""
    org_id = current_user.organization_id

    # Total pipeline runs
    runs_result = await db.execute(
        select(func.count()).select_from(PipelineRun).where(
            PipelineRun.organization_id == org_id
        )
    )
    total_runs = runs_result.scalar() or 0

    # Total raw records extracted
    records_result = await db.execute(
        select(func.count()).select_from(RawRecord).where(
            RawRecord.organization_id == org_id
        )
    )
    total_records = records_result.scalar() or 0

    # Total companies
    companies_result = await db.execute(
        select(func.count()).select_from(Company).where(
            Company.organization_id == org_id
        )
    )
    total_companies = companies_result.scalar() or 0

    # Recent runs (last 5)
    recent_result = await db.execute(
        select(PipelineRun)
        .where(PipelineRun.organization_id == org_id)
        .order_by(PipelineRun.created_at.desc())
        .limit(5)
    )
    recent_runs = list(recent_result.scalars().all())

    return DashboardResponse(
        total_runs=total_runs,
        total_records=total_records,
        total_companies=total_companies,
        recent_runs=[
            RecentRun(
                id=str(run.id),
                query_text=run.query_text,
                status=run.status,
                total_extracted=run.total_extracted,
                created_at=run.created_at,
            )
            for run in recent_runs
        ],
    )
