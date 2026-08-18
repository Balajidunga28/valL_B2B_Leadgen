"""
url: /backend/app/api/level4.py
About:
  Level 4 VALIDATE API endpoint. Triggers the validation pipeline that
  reads cleaned Company records, validates each field, and stores results
  in the company_validations table.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.company_validation import CompanyValidation
from app.api.deps import get_current_user
from app.schemas.level4 import ValidateResponse, CompanyValidationResponse
from app.services.level4 import run_validate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/level4", tags=["level4"])


@router.post("/validate", response_model=ValidateResponse)
async def validate(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute Level 4 VALIDATE pipeline.

    Reads cleaned Company records from Level 3, validates email, phone,
    website, and business existence. Stores results in company_validations.

    Level 3 cleaned records are NOT modified.
    Level 2 raw records are NOT modified.
    Level 5 enrichment is NOT performed.
    """
    try:
        result = await run_validate(
            db=db,
            organization_id=current_user.organization_id,
        )
    except Exception as e:
        logger.error("Level 4 validation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation pipeline failed: {str(e)}",
        )

    return ValidateResponse(**result)


@router.get("/results", response_model=list[CompanyValidationResponse])
async def get_results(
    overall_status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get Level 4 validation results for the organization.

    Optional filter by overall_status (VALID, INVALID, UNKNOWN).
    """
    query = (
        select(CompanyValidation, Company.name)
        .join(Company, CompanyValidation.company_id == Company.id)
        .where(CompanyValidation.organization_id == current_user.organization_id)
    )

    if overall_status:
        query = query.where(CompanyValidation.overall_status == overall_status.upper())

    result = await db.execute(query)
    rows = result.all()

    return [
        CompanyValidationResponse(
            company_id=str(cv.company_id),
            company_name=company_name,
            email_status=cv.email_status,
            phone_status=cv.phone_status,
            website_status=cv.website_status,
            business_existence_status=cv.business_existence_status,
            overall_status=cv.overall_status,
            validation_results=cv.validation_results,
            validated_at=cv.validated_at,
        )
        for cv, company_name in rows
    ]


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary statistics of Level 4 validation results."""
    from sqlalchemy import func

    result = await db.execute(
        select(
            CompanyValidation.overall_status,
            func.count(CompanyValidation.id),
        )
        .where(CompanyValidation.organization_id == current_user.organization_id)
        .group_by(CompanyValidation.overall_status)
    )
    overall_stats = {row[0]: row[1] for row in result.all()}

    result = await db.execute(
        select(
            CompanyValidation.email_status,
            func.count(CompanyValidation.id),
        )
        .where(CompanyValidation.organization_id == current_user.organization_id)
        .group_by(CompanyValidation.email_status)
    )
    email_stats = {row[0]: row[1] for row in result.all()}

    result = await db.execute(
        select(
            CompanyValidation.phone_status,
            func.count(CompanyValidation.id),
        )
        .where(CompanyValidation.organization_id == current_user.organization_id)
        .group_by(CompanyValidation.phone_status)
    )
    phone_stats = {row[0]: row[1] for row in result.all()}

    result = await db.execute(
        select(
            CompanyValidation.website_status,
            func.count(CompanyValidation.id),
        )
        .where(CompanyValidation.organization_id == current_user.organization_id)
        .group_by(CompanyValidation.website_status)
    )
    website_stats = {row[0]: row[1] for row in result.all()}

    result = await db.execute(
        select(
            CompanyValidation.business_existence_status,
            func.count(CompanyValidation.id),
        )
        .where(CompanyValidation.organization_id == current_user.organization_id)
        .group_by(CompanyValidation.business_existence_status)
    )
    business_stats = {row[0]: row[1] for row in result.all()}

    return {
        "overall": overall_stats,
        "email": email_stats,
        "phone": phone_stats,
        "website": website_stats,
        "business_existence": business_stats,
    }
