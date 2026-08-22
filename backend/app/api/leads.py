"""
url: /backend/app/api/leads.py
About:
  Unified Leads API endpoint. Returns complete lead data by joining
  companies, enrichments, validations, and scores in a single query.
  Also supports creating Lead records from discovered companies.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.company_enrichment import CompanyEnrichment
from app.models.company_validation import CompanyValidation
from app.models.lead import Lead
from app.models.lead_score import LeadScore
from app.models.raw_record import RawRecord
from app.api.deps import get_current_user
from app.schemas.leads import LeadResponse, LeadCreateRequest, LeadCreateResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.post("", response_model=LeadCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    request: LeadCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Lead record from a discovered company.
    Captures the current validation, enrichment, and score state.
    If raw_record_id is not provided, finds the first raw record for the company
    from the specified pipeline run.
    """
    # Verify company exists and belongs to organization
    company_result = await db.execute(
        select(Company).where(
            Company.id == request.company_id,
            Company.organization_id == current_user.organization_id,
        )
    )
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Verify pipeline_run exists and belongs to organization
    from app.models.pipeline_run import PipelineRun
    run_result = await db.execute(
        select(PipelineRun).where(
            PipelineRun.id == request.pipeline_run_id,
            PipelineRun.organization_id == current_user.organization_id,
        )
    )
    pipeline_run = run_result.scalar_one_or_none()
    if not pipeline_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline run not found",
        )

    # Determine raw_record_id
    raw_record_id = request.raw_record_id
    if not raw_record_id:
        # Find the first raw record for this company from this pipeline run
        raw_record_result = await db.execute(
            select(RawRecord.id).where(
                RawRecord.company_id == request.company_id,
                RawRecord.pipeline_run_id == request.pipeline_run_id,
                RawRecord.organization_id == current_user.organization_id,
            ).limit(1)
        )
        raw_record_id = raw_record_result.scalar_one_or_none()
        if not raw_record_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No raw record found for this company in the specified pipeline run",
            )
    else:
        # Verify provided raw_record exists and belongs to organization
        raw_record_result = await db.execute(
            select(RawRecord).where(
                RawRecord.id == raw_record_id,
                RawRecord.organization_id == current_user.organization_id,
            )
        )
        raw_record = raw_record_result.scalar_one_or_none()
        if not raw_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Raw record not found",
            )

    # Check if lead already exists for this company + pipeline_run + raw_record
    existing_lead_result = await db.execute(
        select(Lead).where(
            Lead.company_id == request.company_id,
            Lead.pipeline_run_id == request.pipeline_run_id,
            Lead.raw_record_id == raw_record_id,
            Lead.organization_id == current_user.organization_id,
        )
    )
    existing_lead = existing_lead_result.scalar_one_or_none()
    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lead already exists for this discovery",
        )

    # Get validation status
    validation_result = await db.execute(
        select(CompanyValidation).where(
            CompanyValidation.company_id == request.company_id,
        )
    )
    validation = validation_result.scalar_one_or_none()
    validation_status = validation.overall_status if validation else "pending"

    # Get enrichment status
    enrichment_result = await db.execute(
        select(CompanyEnrichment).where(
            CompanyEnrichment.company_id == request.company_id,
        )
    )
    enrichment = enrichment_result.scalar_one_or_none()
    enrichment_status = "completed" if enrichment else "pending"

    # Get lead score
    score_result = await db.execute(
        select(LeadScore).where(
            LeadScore.company_id == request.company_id,
        )
    )
    lead_score = score_result.scalar_one_or_none()

    # Create Lead record
    lead = Lead(
        organization_id=current_user.organization_id,
        company_id=request.company_id,
        pipeline_run_id=request.pipeline_run_id,
        raw_record_id=raw_record_id,
        validation_status=validation_status,
        validation_issues=validation.validation_issues if validation else None,
        enrichment_status=enrichment_status,
        lead_score=lead_score.total_score if lead_score else None,
        score_version=lead_score.score_version if lead_score else None,
        score_components={
            "industry_score": float(lead_score.industry_score) if lead_score and lead_score.industry_score else None,
            "size_score": float(lead_score.size_score) if lead_score and lead_score.size_score else None,
            "location_score": float(lead_score.location_score) if lead_score and lead_score.location_score else None,
            "technology_score": float(lead_score.technology_score) if lead_score and lead_score.technology_score else None,
            "data_quality_score": float(lead_score.data_quality_score) if lead_score and lead_score.data_quality_score else None,
            "validation_score": float(lead_score.validation_score) if lead_score and lead_score.validation_score else None,
        } if lead_score else None,
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    logger.info("Created lead %s for company %s from pipeline run %s",
                lead.id, request.company_id, request.pipeline_run_id)

    return LeadCreateResponse(
        id=str(lead.id),
        company_id=str(lead.company_id),
        pipeline_run_id=str(lead.pipeline_run_id),
        raw_record_id=str(lead.raw_record_id),
        validation_status=lead.validation_status,
        enrichment_status=lead.enrichment_status,
        lead_score=float(lead.lead_score) if lead.lead_score is not None else None,
        score_version=lead.score_version,
        created_at=lead.created_at,
    )


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
    # Subquery: all source_adapters per company
    source_subq = (
        select(
            RawRecord.company_id,
            func.array_agg(func.distinct(RawRecord.source_adapter)).label("source_adapters"),
        )
        .where(RawRecord.company_id.isnot(None))
        .group_by(RawRecord.company_id)
    ).subquery()

    # Subquery: check if Lead record exists for company
    lead_exists_subq = (
        select(
            Lead.company_id,
            func.count(Lead.id).label("lead_count"),
        )
        .where(Lead.organization_id == current_user.organization_id)
        .group_by(Lead.company_id)
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
        except (ValueError, Exception):
            pass

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
            source_subq.c.source_adapters,
            CompanyValidation.overall_status,
            CompanyEnrichment.description,
            CompanyEnrichment.email,
            CompanyEnrichment.social_links,
            LeadScore.total_score,
            LeadScore.score_version,
            LeadScore.scored_at,
            lead_exists_subq.c.lead_count,
        )
        .outerjoin(CompanyEnrichment, CompanyEnrichment.company_id == Company.id)
        .outerjoin(CompanyValidation, CompanyValidation.company_id == Company.id)
        .outerjoin(LeadScore, LeadScore.company_id == Company.id)
        .outerjoin(source_subq, source_subq.c.company_id == Company.id)
        .outerjoin(lead_exists_subq, lead_exists_subq.c.company_id == Company.id)
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
        query = query.where(source_subq.c.source_adapters.contains([source]))

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
            source=(row[13][0] if row[13] else None),
            sources=(row[13] if row[13] else []),
            validation_status=row[14],
            enrichment_description=row[15],
            enrichment_email=row[16],
            enrichment_social_links=row[17],
            total_score=float(row[18]) if row[18] is not None else None,
            score_version=row[19],
            scored_at=row[20],
            is_saved=row[21] is not None and row[21] > 0,
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
    # Subquery: all source_adapters per company
    source_subq = (
        select(
            RawRecord.company_id,
            func.array_agg(func.distinct(RawRecord.source_adapter)).label("source_adapters"),
        )
        .where(RawRecord.company_id.isnot(None))
        .group_by(RawRecord.company_id)
    ).subquery()

    # Subquery: check if Lead record exists for company
    lead_exists_subq = (
        select(
            Lead.company_id,
            func.count(Lead.id).label("lead_count"),
        )
        .where(Lead.organization_id == current_user.organization_id)
        .group_by(Lead.company_id)
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
            source_subq.c.source_adapters,
            CompanyValidation.overall_status,
            CompanyEnrichment.description,
            CompanyEnrichment.email,
            CompanyEnrichment.social_links,
            LeadScore.total_score,
            LeadScore.score_version,
            LeadScore.scored_at,
            lead_exists_subq.c.lead_count,
        )
        .outerjoin(CompanyEnrichment, CompanyEnrichment.company_id == Company.id)
        .outerjoin(CompanyValidation, CompanyValidation.company_id == Company.id)
        .outerjoin(LeadScore, LeadScore.company_id == Company.id)
        .outerjoin(source_subq, source_subq.c.company_id == Company.id)
        .outerjoin(lead_exists_subq, lead_exists_subq.c.company_id == Company.id)
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
        source=(row[13][0] if row[13] else None),
        sources=(row[13] if row[13] else []),
        validation_status=row[14],
        enrichment_description=row[15],
        enrichment_email=row[16],
        enrichment_social_links=row[17],
        total_score=float(row[18]) if row[18] is not None else None,
        score_version=row[19],
        scored_at=row[20],
        is_saved=row[21] is not None and row[21] > 0,
    )
