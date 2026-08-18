"""
url: /backend/app/api/level5.py
About:
  Level 5 ENRICH API endpoint. Triggers the enrichment pipeline that
  reads validated Company records and enriches them with additional data.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.company_enrichment import CompanyEnrichment
from app.api.deps import get_current_user
from app.schemas.level5 import EnrichResponse, CompanyEnrichmentResponse
from app.services.level5 import run_enrich

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/level5", tags=["level5"])


@router.post("/enrich", response_model=EnrichResponse)
async def enrich(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute Level 5 ENRICH pipeline.

    Reads validated Company records, enriches with website scraping,
    name-based industry inference, and metadata extraction.
    Stores results in company_enrichments.

    Levels 2-4 are NOT modified.
    """
    try:
        result = await run_enrich(
            db=db,
            organization_id=current_user.organization_id,
        )
    except Exception as e:
        logger.error("Level 5 enrichment failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment pipeline failed: {str(e)}",
        )

    return EnrichResponse(**result)


@router.get("/results", response_model=list[CompanyEnrichmentResponse])
async def get_results(
    has_industry: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get Level 5 enrichment results for the organization."""
    query = (
        select(CompanyEnrichment, Company.name)
        .join(Company, CompanyEnrichment.company_id == Company.id)
        .where(CompanyEnrichment.organization_id == current_user.organization_id)
    )

    if has_industry is True:
        query = query.where(CompanyEnrichment.industry.isnot(None))
    elif has_industry is False:
        query = query.where(CompanyEnrichment.industry.is_(None))

    result = await db.execute(query)
    rows = result.all()

    return [
        CompanyEnrichmentResponse(
            company_id=str(ce.company_id),
            company_name=company_name,
            industry=ce.industry,
            industry_source=ce.industry_source,
            company_size=ce.company_size,
            founded_year=ce.founded_year,
            description=ce.description,
            social_links=ce.social_links,
            email=ce.email,
            additional_phones=ce.additional_phones,
            enriched_at=ce.enriched_at,
        )
        for ce, company_name in rows
    ]


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary statistics of Level 5 enrichment results."""
    total = await db.execute(
        select(func.count(CompanyEnrichment.id)).where(
            CompanyEnrichment.organization_id == current_user.organization_id
        )
    )
    total_count = total.scalar()

    industry_count = await db.execute(
        select(func.count(CompanyEnrichment.id)).where(
            CompanyEnrichment.organization_id == current_user.organization_id,
            CompanyEnrichment.industry.isnot(None),
        )
    )
    social_count = await db.execute(
        select(func.count(CompanyEnrichment.id)).where(
            CompanyEnrichment.organization_id == current_user.organization_id,
            CompanyEnrichment.social_links.isnot(None),
        )
    )
    email_count = await db.execute(
        select(func.count(CompanyEnrichment.id)).where(
            CompanyEnrichment.organization_id == current_user.organization_id,
            CompanyEnrichment.email.isnot(None),
        )
    )
    desc_count = await db.execute(
        select(func.count(CompanyEnrichment.id)).where(
            CompanyEnrichment.organization_id == current_user.organization_id,
            CompanyEnrichment.description.isnot(None),
        )
    )
    founded_count = await db.execute(
        select(func.count(CompanyEnrichment.id)).where(
            CompanyEnrichment.organization_id == current_user.organization_id,
            CompanyEnrichment.founded_year.isnot(None),
        )
    )

    return {
        "total_enrichments": total_count,
        "with_industry": industry_count.scalar(),
        "with_social_links": social_count.scalar(),
        "with_email": email_count.scalar(),
        "with_description": desc_count.scalar(),
        "with_founded_year": founded_count.scalar(),
    }
