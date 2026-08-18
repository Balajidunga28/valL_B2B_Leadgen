"""
url: /backend/app/services/level6.py
About:
  Level 6 SCORE pipeline orchestrator. Reads enriched companies with their
  validation results and produces lead scores. Filtering is query-time only —
  no records are deleted.

  Level 6 does NOT:
  - Modify raw_records (Level 2)
  - Modify companies (Level 3)
  - Modify company_validations (Level 4)
  - Modify company_enrichments (Level 5)
  - Delete any records
"""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_enrichment import CompanyEnrichment
from app.models.company_validation import CompanyValidation
from app.models.lead_score import LeadScore
from app.services.score import score_company, SCORE_VERSION

logger = logging.getLogger(__name__)


async def run_score(
    db: AsyncSession,
    organization_id,
) -> dict:
    """Execute Level 6 SCORE pipeline.

    1. Read all companies with their enrichments and validations
    2. Score each company using the documented formula
    3. Store results in lead_scores table

    Returns a summary dict with counts.
    """
    # --- Step 1: Read all companies with enrichments and validations ---
    result = await db.execute(
        select(Company).where(Company.organization_id == organization_id)
    )
    companies = list(result.scalars().all())

    if not companies:
        logger.info("Level 6: No companies found for organization %s", organization_id)
        return {
            "companies_read": 0,
            "scored": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "min_score": 0,
            "max_score": 0,
            "avg_score": 0,
        }

    logger.info("Level 6: Scoring %d companies for organization %s",
                len(companies), organization_id)

    # --- Step 2: Clear previous scores ---
    await db.execute(
        delete(LeadScore).where(LeadScore.organization_id == organization_id)
    )
    await db.flush()

    # --- Step 3: Score each company ---
    stats = {
        "scored": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    all_scores = []

    for company in companies:
        # Gather enrichment data
        enrichment = None
        if company.enrichments:
            enrichment = company.enrichments[0] if company.enrichments else None

        # Gather validation data
        validation = None
        if company.validations:
            validation = company.validations[0] if company.validations else None

        # Build data dicts for scoring
        company_data = {
            "phone": company.phone,
            "website": company.website,
            "city": company.city,
            "address": company.address,
            "latitude": company.latitude,
            "longitude": company.longitude,
            "rating": company.rating,
            "review_count": company.review_count,
        }

        enrichment_data = {
            "industry": enrichment.industry if enrichment else None,
            "company_size": enrichment.company_size if enrichment else None,
            "technologies": enrichment.technologies if enrichment else None,
            "email": enrichment.email if enrichment else None,
            "description": enrichment.description if enrichment else None,
            "social_links": enrichment.social_links if enrichment else None,
        }

        validation_data = {
            "overall_status": validation.overall_status if validation else None,
        }

        # Score
        scores = score_company(company_data, enrichment_data, validation_data)

        # Create LeadScore record
        lead_score = LeadScore(
            id=uuid4(),
            organization_id=organization_id,
            company_id=company.id,
            industry_score=scores["industry_score"],
            size_score=scores["size_score"],
            location_score=scores["location_score"],
            technology_score=scores["technology_score"],
            data_quality_score=scores["data_quality_score"],
            validation_score=scores["validation_score"],
            total_score=scores["total_score"],
            score_version=scores["score_version"],
            scoring_formula=scores["scoring_formula"],
            scored_at=datetime.now(timezone.utc),
        )
        db.add(lead_score)
        stats["scored"] += 1
        all_scores.append(float(scores["total_score"]))

        # Tier classification
        total = float(scores["total_score"])
        if total >= 60:
            stats["high"] += 1
        elif total >= 35:
            stats["medium"] += 1
        else:
            stats["low"] += 1

    await db.commit()

    # Compute stats
    if all_scores:
        stats["min_score"] = round(min(all_scores), 2)
        stats["max_score"] = round(max(all_scores), 2)
        stats["avg_score"] = round(sum(all_scores) / len(all_scores), 2)
    else:
        stats["min_score"] = 0
        stats["max_score"] = 0
        stats["avg_score"] = 0

    logger.info("Level 6: Scored %d companies — high=%d, medium=%d, low=%d",
                stats["scored"], stats["high"], stats["medium"], stats["low"])

    return {
        "companies_read": len(companies),
        **stats,
    }
