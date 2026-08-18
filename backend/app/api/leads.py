"""
url: /backend/app/api/leads.py
About:
  Unified Leads API endpoint. Returns complete lead data by joining
  companies, enrichments, validations, and scores in a single query.
  Read-only — no data modification.
"""

import logging

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.company_enrichment import CompanyEnrichment
from app.models.company_validation import CompanyValidation
from app.models.lead_score import LeadScore
from app.models.raw_record import RawRecord
from app.api.deps import get_current_user
from app.schemas.leads import LeadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    search_id: str | None = Query(None, description="Pipeline run ID to scope results to"),
    min_score: float | None = Query(None, description="Minimum total score"),
    max_score: float | None = Query(None, description="Maximum total score"),
    industry: str | None = Query(None, description="Industry filter"),
    has_phone: bool | None = Query(None, description="Has phone number"),
    has_email: bool | None = Query(None, description="Has email"),
    has_website: bool | None = Query(None, description="Has website"),
    validation_status: str | None = Query(None, description="Validation status"),
    city: str | None = Query(None, description="City filter"),
    source: str | None = Query(None, description="Source adapter filter"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List complete leads with filtering. Joins company, enrichment,
    validation, and score data in a single query.
    """
    # Subquery: first source_adapter per company
    source_subq = (
        select(
            RawRecord.company_id,
            func.min(RawRecord.source_adapter).label("source_adapter"),
        )
        .where(RawRecord.company_id.isnot(None))
        .group_by(RawRecord.company_id)
    ).subquery()

    # Subquery: company IDs linked to a specific pipeline_run (via raw_records)
    search_company_subq = None
    if search_id:
        from uuid import UUID
        try:
            run_uuid = UUID(search_id)
            search_company_subq = (
                select(RawRecord.company_id)
                .where(RawRecord.pipeline_run_id == run_uuid)
                .where(RawRecord.company_id.isnot(None))
                .distinct()
            ).subquery()

    query = (
        select(
            Company.id,
            Company.name,
            CompanyEnrichment.industry,
            Company.address,
            Company.city,
            Company.state,
            Company.country,
            Company.phone,
            Company.website,
            Company.rating,
            Company.review_count,
            Company.latitude,
            Company.longitude,
            source_subq.c.source_adapter,
            CompanyValidation.overall_status,
            CompanyEnrichment.description,
            CompanyEnrichment.email,
            CompanyEnrichment.social_links,
            LeadScore.total_score,
            LeadScore.score_version,
            LeadScore.scored_at,
        )
        .outerjoin(CompanyEnrichment, CompanyEnrichment.company_id == Company.id)
        .outerjoin(CompanyValidation, CompanyValidation.company_id == Company.id)
        .outerjoin(LeadScore, LeadScore.company_id == Company.id)
        .outerjoin(source_subq, source_subq.c.company_id == Company.id)
        .where(Company.organization_id == current_user.organization_id)
    )

    if search_company_subq is not None:
        query = query.where(Company.id.in_(select(search_company_subq.c.company_id)))

    # Apply filters
    if min_score is not None:
        query = query.where(LeadScore.total_score >= min_score)
    if max_score is not None:
        query = query.where(LeadScore.total_score <= max_score)
    if industry:
        query = query.where(CompanyEnrichment.industry.ilike(f"%{industry}%"))
    if has_phone is True:
        query = query.where(Company.phone.isnot(None))
    elif has_phone is False:
        query = query.where(Company.phone.is_(None))
    if has_email is True:
        query = query.where(CompanyEnrichment.email.isnot(None))
    elif has_email is False:
        query = query.where(CompanyEnrichment.email.is_(None))
    if has_website is True:
        query = query.where(Company.website.isnot(None))
    elif has_website is False:
        query = query.where(Company.website.is_(None))
    if validation_status:
        query = query.where(
            CompanyValidation.overall_status == validation_status.upper()
        )
    if city:
        query = query.where(Company.city.ilike(f"%{city}%"))
    if source:
        query = query.where(source_subq.c.source_adapter == source)

    query = query.order_by(LeadScore.total_score.desc().nullslast())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        LeadResponse(
            id=str(row[0]),
            name=row[1],
            industry=row[2],
            address=row[3],
            city=row[4],
            state=row[5],
            country=row[6],
            phone=row[7],
            website=row[8],
            rating=float(row[9]) if row[9] else None,
            review_count=int(row[10]) if row[10] else None,
            latitude=float(row[11]) if row[11] else None,
            longitude=float(row[12]) if row[12] else None,
            source=row[13],
            validation_status=row[14],
            enrichment_description=row[15],
            enrichment_email=row[16],
            enrichment_social_links=row[17],
            total_score=float(row[18]) if row[18] is not None else None,
            score_version=row[19],
            scored_at=row[20],
        )
        for row in rows
    ]


@router.get("/stats")
async def lead_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary statistics for the leads list."""
    total = await db.execute(
        select(func.count(Company.id)).where(
            Company.organization_id == current_user.organization_id
        )
    )
    with_score = await db.execute(
        select(func.count(LeadScore.id))
        .join(Company, LeadScore.company_id == Company.id)
        .where(Company.organization_id == current_user.organization_id)
    )
    with_phone = await db.execute(
        select(func.count(Company.id)).where(
            Company.organization_id == current_user.organization_id,
            Company.phone.isnot(None),
        )
    )
    with_industry = await db.execute(
        select(func.count(CompanyEnrichment.id))
        .join(Company, CompanyEnrichment.company_id == Company.id)
        .where(
            Company.organization_id == current_user.organization_id,
            CompanyEnrichment.industry.isnot(None),
        )
    )

    return {
        "total_companies": total.scalar(),
        "with_score": with_score.scalar(),
        "with_phone": with_phone.scalar(),
        "with_industry": with_industry.scalar(),
    }


@router.get("/{company_id}", response_model=LeadResponse)
async def get_lead(
    company_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single lead by company ID."""
    # Subquery: first source_adapter per company
    source_subq = (
        select(
            RawRecord.company_id,
            func.min(RawRecord.source_adapter).label("source_adapter"),
        )
        .where(RawRecord.company_id.isnot(None))
        .group_by(RawRecord.company_id)
    ).subquery()

    query = (
        select(
            Company.id,
            Company.name,
            CompanyEnrichment.industry,
            Company.address,
            Company.city,
            Company.state,
            Company.country,
            Company.phone,
            Company.website,
            Company.rating,
            Company.review_count,
            Company.latitude,
            Company.longitude,
            source_subq.c.source_adapter,
            CompanyValidation.overall_status,
            CompanyEnrichment.description,
            CompanyEnrichment.email,
            CompanyEnrichment.social_links,
            LeadScore.total_score,
            LeadScore.score_version,
            LeadScore.scored_at,
        )
        .outerjoin(CompanyEnrichment, CompanyEnrichment.company_id == Company.id)
        .outerjoin(CompanyValidation, CompanyValidation.company_id == Company.id)
        .outerjoin(LeadScore, LeadScore.company_id == Company.id)
        .outerjoin(source_subq, source_subq.c.company_id == Company.id)
        .where(Company.id == company_id)
        .where(Company.organization_id == current_user.organization_id)
    )

    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return LeadResponse(
        id=str(row[0]),
        name=row[1],
        industry=row[2],
        address=row[3],
        city=row[4],
        state=row[5],
        country=row[6],
        phone=row[7],
        website=row[8],
        rating=float(row[9]) if row[9] else None,
        review_count=int(row[10]) if row[10] else None,
        latitude=float(row[11]) if row[11] else None,
        longitude=float(row[12]) if row[12] else None,
        source=row[13],
        validation_status=row[14],
        enrichment_description=row[15],
        enrichment_email=row[16],
        enrichment_social_links=row[17],
        total_score=float(row[18]) if row[18] is not None else None,
        score_version=row[19],
        scored_at=row[20],
    )
