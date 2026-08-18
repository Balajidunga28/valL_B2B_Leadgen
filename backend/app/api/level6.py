"""
url: /backend/app/api/level6.py
About:
  Level 6 SCORE/Filter API endpoint. Provides scoring pipeline execution,
  score retrieval with filtering, and summary statistics.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.company_enrichment import CompanyEnrichment
from app.models.company_validation import CompanyValidation
from app.models.lead_score import LeadScore
from app.api.deps import get_current_user
from app.schemas.level6 import ScoreResponse, LeadScoreResponse, FilterRequest
from app.services.level6 import run_score

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/level6", tags=["level6"])


@router.post("/score", response_model=ScoreResponse)
async def score(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute Level 6 SCORE pipeline.

    Reads enriched companies with validation results and produces
    lead scores. Filtering is query-time only — no records deleted.
    """
    try:
        result = await run_score(
            db=db,
            organization_id=current_user.organization_id,
        )
    except Exception as e:
        logger.error("Level 6 scoring failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring pipeline failed: {str(e)}",
        )

    return ScoreResponse(**result)


@router.get("/leads", response_model=list[LeadScoreResponse])
async def get_leads(
    min_score: float | None = Query(None, description="Minimum total score"),
    max_score: float | None = Query(None, description="Maximum total score"),
    industry: str | None = Query(None, description="Industry filter"),
    has_phone: bool | None = Query(None, description="Has phone number"),
    has_email: bool | None = Query(None, description="Has email"),
    has_website: bool | None = Query(None, description="Has website"),
    validation_status: str | None = Query(None, description="Validation status"),
    city: str | None = Query(None, description="City filter"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get scored leads with optional filtering.

    Filtering is query-time — all scored leads remain stored.
    """
    query = (
        select(LeadScore, Company.name)
        .join(Company, LeadScore.company_id == Company.id)
        .where(LeadScore.organization_id == current_user.organization_id)
    )

    # Score range filter
    if min_score is not None:
        query = query.where(LeadScore.total_score >= min_score)
    if max_score is not None:
        query = query.where(LeadScore.total_score <= max_score)

    # Industry filter (via enrichment)
    if industry:
        query = query.join(
            CompanyEnrichment, CompanyEnrichment.company_id == Company.id
        ).where(CompanyEnrichment.industry.ilike(f"%{industry}%"))

    # Phone filter
    if has_phone is True:
        query = query.where(Company.phone.isnot(None))
    elif has_phone is False:
        query = query.where(Company.phone.is_(None))

    # Email filter (via enrichment)
    if has_email is True:
        query = query.join(
            CompanyEnrichment, CompanyEnrichment.company_id == Company.id
        ).where(CompanyEnrichment.email.isnot(None))
    elif has_email is False:
        query = query.join(
            CompanyEnrichment, CompanyEnrichment.company_id == Company.id
        ).where(CompanyEnrichment.email.is_(None))

    # Website filter
    if has_website is True:
        query = query.where(Company.website.isnot(None))
    elif has_website is False:
        query = query.where(Company.website.is_(None))

    # Validation status filter
    if validation_status:
        query = query.join(
            CompanyValidation, CompanyValidation.company_id == Company.id
        ).where(CompanyValidation.overall_status == validation_status.upper())

    # City filter
    if city:
        query = query.where(Company.city.ilike(f"%{city}%"))

    # Order by score descending
    query = query.order_by(LeadScore.total_score.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        LeadScoreResponse(
            company_id=str(ls.company_id),
            company_name=company_name,
            industry_score=float(ls.industry_score),
            size_score=float(ls.size_score),
            location_score=float(ls.location_score),
            technology_score=float(ls.technology_score),
            data_quality_score=float(ls.data_quality_score),
            validation_score=float(ls.validation_score),
            total_score=float(ls.total_score),
            score_version=ls.score_version,
            scored_at=ls.scored_at,
        )
        for ls, company_name in rows
    ]


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary statistics of Level 6 scoring results."""
    total = await db.execute(
        select(func.count(LeadScore.id)).where(
            LeadScore.organization_id == current_user.organization_id
        )
    )
    total_count = total.scalar()

    avg = await db.execute(
        select(func.avg(LeadScore.total_score)).where(
            LeadScore.organization_id == current_user.organization_id
        )
    )
    avg_score = float(avg.scalar() or 0)

    high = await db.execute(
        select(func.count(LeadScore.id)).where(
            LeadScore.organization_id == current_user.organization_id,
            LeadScore.total_score >= 60,
        )
    )
    medium = await db.execute(
        select(func.count(LeadScore.id)).where(
            LeadScore.organization_id == current_user.organization_id,
            LeadScore.total_score >= 35,
            LeadScore.total_score < 60,
        )
    )
    low = await db.execute(
        select(func.count(LeadScore.id)).where(
            LeadScore.organization_id == current_user.organization_id,
            LeadScore.total_score < 35,
        )
    )

    min_s = await db.execute(
        select(func.min(LeadScore.total_score)).where(
            LeadScore.organization_id == current_user.organization_id
        )
    )
    max_s = await db.execute(
        select(func.max(LeadScore.total_score)).where(
            LeadScore.organization_id == current_user.organization_id
        )
    )

    return {
        "total_scored": total_count,
        "high": high.scalar(),
        "medium": medium.scalar(),
        "low": low.scalar(),
        "avg_score": round(avg_score, 2),
        "min_score": float(min_s.scalar() or 0),
        "max_score": float(max_s.scalar() or 0),
    }
