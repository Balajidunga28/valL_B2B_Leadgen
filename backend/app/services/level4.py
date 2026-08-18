"""
url: /backend/app/services/level4.py
About:
  Level 4 VALIDATE pipeline orchestrator. Reads cleaned Company records
  from Level 3, validates each field (email, phone, website, business
  existence), and stores results in the company_validations table.

  Level 4 does NOT:
  - Modify raw_records (Level 2)
  - Modify companies (Level 3)
  - Enrich with external data (Level 5)
  - Score or filter leads (Level 6)
  - Export data (Level 7)
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_validation import CompanyValidation
from app.models.raw_record import RawRecord
from app.services.validate import (
    validate_email, validate_phone, validate_website,
    validate_business_existence, VALID, INVALID, UNKNOWN, NOT_AVAILABLE,
)

logger = logging.getLogger(__name__)


def _compute_overall_status(
    email_status: str,
    phone_status: str,
    website_status: str,
    business_existence_status: str,
) -> str:
    """Compute overall validation status from per-field statuses.

    Logic:
    - If business_existence is INVALID -> overall INVALID
    - If business_existence is UNKNOWN and no other field is VALID -> UNKNOWN
    - If at least one field is VALID and business is not INVALID -> VALID
    - Otherwise -> UNKNOWN
    """
    statuses = [email_status, phone_status, website_status]

    if business_existence_status == INVALID:
        return INVALID

    if business_existence_status == UNKNOWN and VALID not in statuses:
        return UNKNOWN

    if VALID in statuses and business_existence_status != INVALID:
        return VALID

    if business_existence_status == NOT_AVAILABLE and all(
        s in (NOT_AVAILABLE, UNKNOWN) for s in statuses
    ):
        return UNKNOWN

    return UNKNOWN


async def run_validate(
    db: AsyncSession,
    organization_id,
) -> dict:
    """Execute Level 4 VALIDATE pipeline.

    1. Read all companies for the organization
    2. For each company, load its raw_records to get source_adapters
    3. Validate email, phone, website, business existence
    4. Store results in company_validations table

    Returns a summary dict with counts.
    """
    # --- Step 1: Read all companies ---
    result = await db.execute(
        select(Company).where(Company.organization_id == organization_id)
    )
    companies = list(result.scalars().all())

    if not companies:
        logger.info("Level 4: No companies found for organization %s", organization_id)
        return {
            "companies_read": 0,
            "validated": 0,
            "valid": 0,
            "invalid": 0,
            "unknown": 0,
            "email_valid": 0,
            "email_invalid": 0,
            "email_not_available": 0,
            "phone_valid": 0,
            "phone_invalid": 0,
            "phone_not_available": 0,
            "website_valid": 0,
            "website_invalid": 0,
            "website_not_available": 0,
            "business_valid": 0,
            "business_invalid": 0,
            "business_unknown": 0,
        }

    logger.info("Level 4: Validating %d companies for organization %s",
                len(companies), organization_id)

    # --- Step 2: Clear previous validation results ---
    await db.execute(
        delete(CompanyValidation).where(
            CompanyValidation.organization_id == organization_id
        )
    )
    await db.flush()

    # --- Step 3: Validate each company ---
    stats = {
        "validated": 0,
        "valid": 0,
        "invalid": 0,
        "unknown": 0,
        "email_valid": 0,
        "email_invalid": 0,
        "email_not_available": 0,
        "email_unknown": 0,
        "phone_valid": 0,
        "phone_invalid": 0,
        "phone_not_available": 0,
        "phone_unknown": 0,
        "website_valid": 0,
        "website_invalid": 0,
        "website_not_available": 0,
        "website_unknown": 0,
        "business_valid": 0,
        "business_invalid": 0,
        "business_unknown": 0,
    }

    for company in companies:
        # Load raw_records for this company to get source_adapters
        source_adapters = []
        if company.raw_records:
            source_adapters = list({rr.source_adapter for rr in company.raw_records})

        # --- Email validation ---
        # Email is not on companies table — check raw_data from linked raw_records
        email = None
        if company.raw_records:
            for rr in company.raw_records:
                raw_email = (rr.raw_data or {}).get("email")
                if raw_email and str(raw_email).strip():
                    email = raw_email
                    break

        email_status, email_details = validate_email(email)

        # --- Phone validation ---
        phone_status, phone_details = validate_phone(company.phone)

        # --- Website validation ---
        website_status, website_details = validate_website(company.website)

        # --- Business existence validation ---
        biz_status, biz_details = validate_business_existence(
            name=company.name,
            phone=company.phone,
            address=company.address,
            city=company.city,
            latitude=float(company.latitude) if company.latitude else None,
            longitude=float(company.longitude) if company.longitude else None,
            website=company.website,
            rating=float(company.rating) if company.rating else None,
            source_adapters=source_adapters,
        )

        # --- Overall status ---
        overall = _compute_overall_status(
            email_status, phone_status, website_status, biz_status
        )

        # --- Create validation record ---
        validation = CompanyValidation(
            id=uuid4(),
            organization_id=organization_id,
            company_id=company.id,
            email_status=email_status,
            phone_status=phone_status,
            website_status=website_status,
            business_existence_status=biz_status,
            overall_status=overall,
            validation_results={
                "email": email_details,
                "phone": phone_details,
                "website": website_details,
                "business_existence": biz_details,
            },
            validation_errors=None,
            validated_at=datetime.now(timezone.utc),
        )
        db.add(validation)
        stats["validated"] += 1

        # Update stats
        overall_key = overall.lower()
        if overall_key in stats:
            stats[overall_key] += 1

        email_key = f"email_{email_status.lower()}"
        if email_key in stats:
            stats[email_key] += 1

        phone_key = f"phone_{phone_status.lower()}"
        if phone_key in stats:
            stats[phone_key] += 1

        website_key = f"website_{website_status.lower()}"
        if website_key in stats:
            stats[website_key] += 1

        biz_key = f"business_{biz_status.lower()}"
        if biz_key in stats:
            stats[biz_key] += 1

    await db.commit()

    logger.info("Level 4: Validated %d companies — valid=%d, invalid=%d, unknown=%d",
                stats["validated"], stats["valid"], stats["invalid"], stats["unknown"])

    return {
        "companies_read": len(companies),
        **stats,
    }
