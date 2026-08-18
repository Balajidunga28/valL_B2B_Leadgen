"""
url: /backend/app/services/level7.py
About:
  Level 7 EXPORT service. Generates CSV exports of scored/filtered lead
  data from Level 6. Read-only — does not modify any data.

  Supports the same filtering parameters as Level 6 leads endpoint.
  Produces UTF-8 CSV with proper escaping and stable column ordering.
"""

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_enrichment import CompanyEnrichment
from app.models.company_validation import CompanyValidation
from app.models.lead_score import LeadScore

logger = logging.getLogger(__name__)

# CSV columns in stable order
CSV_COLUMNS = [
    "company_name",
    "industry",
    "address",
    "city",
    "state",
    "country",
    "phone",
    "email",
    "website",
    "source",
    "source_url",
    "rating",
    "review_count",
    "latitude",
    "longitude",
    "validation_status",
    "enrichment_description",
    "enrichment_social_links",
    "enrichment_founded_year",
    "industry_score",
    "size_score",
    "location_score",
    "technology_score",
    "data_quality_score",
    "validation_score",
    "total_score",
    "score_version",
]


def _val(v: Any) -> str:
    """Convert a value to CSV-safe string. None -> empty string."""
    if v is None:
        return ""
    if isinstance(v, dict):
        import json
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        import json
        return json.dumps(v, ensure_ascii=False)
    return str(v)


async def build_export_query(
    db: AsyncSession,
    organization_id,
    min_score: float | None = None,
    max_score: float | None = None,
    industry: str | None = None,
    has_phone: bool | None = None,
    has_email: bool | None = None,
    has_website: bool | None = None,
    validation_status: str | None = None,
    city: str | None = None,
):
    """Build a query for scored leads with filters. Returns (query, applied_filters)."""
    query = (
        select(
            LeadScore,
            Company.name,
            Company.phone,
            Company.website,
            Company.city,
            Company.state,
            Company.country,
            Company.address,
            Company.latitude,
            Company.longitude,
            Company.rating,
            Company.review_count,
            CompanyEnrichment.industry,
            CompanyEnrichment.email,
            CompanyEnrichment.description,
            CompanyEnrichment.social_links,
            CompanyEnrichment.founded_year,
            CompanyValidation.overall_status,
        )
        .join(Company, LeadScore.company_id == Company.id)
        .outerjoin(CompanyEnrichment, CompanyEnrichment.company_id == Company.id)
        .outerjoin(CompanyValidation, CompanyValidation.company_id == Company.id)
        .where(LeadScore.organization_id == organization_id)
    )

    applied_filters = {}

    if min_score is not None:
        query = query.where(LeadScore.total_score >= min_score)
        applied_filters["min_score"] = min_score
    if max_score is not None:
        query = query.where(LeadScore.total_score <= max_score)
        applied_filters["max_score"] = max_score
    if industry:
        query = query.where(CompanyEnrichment.industry.ilike(f"%{industry}%"))
        applied_filters["industry"] = industry
    if has_phone is True:
        query = query.where(Company.phone.isnot(None))
        applied_filters["has_phone"] = True
    elif has_phone is False:
        query = query.where(Company.phone.is_(None))
        applied_filters["has_phone"] = False
    if has_email is True:
        query = query.where(CompanyEnrichment.email.isnot(None))
        applied_filters["has_email"] = True
    elif has_email is False:
        query = query.where(CompanyEnrichment.email.is_(None))
        applied_filters["has_email"] = False
    if has_website is True:
        query = query.where(Company.website.isnot(None))
        applied_filters["has_website"] = True
    elif has_website is False:
        query = query.where(Company.website.is_(None))
        applied_filters["has_website"] = False
    if validation_status:
        query = query.where(CompanyValidation.overall_status == validation_status.upper())
        applied_filters["validation_status"] = validation_status.upper()
    if city:
        query = query.where(Company.city.ilike(f"%{city}%"))
        applied_filters["city"] = city

    query = query.order_by(LeadScore.total_score.desc())

    return query, applied_filters


async def export_leads_csv(
    db: AsyncSession,
    organization_id,
    min_score: float | None = None,
    max_score: float | None = None,
    industry: str | None = None,
    has_phone: bool | None = None,
    has_email: bool | None = None,
    has_website: bool | None = None,
    validation_status: str | None = None,
    city: str | None = None,
) -> tuple[str, int, dict]:
    """Export scored leads as CSV string.

    Returns (csv_string, record_count, applied_filters).
    """
    query, applied_filters = await build_export_query(
        db, organization_id,
        min_score=min_score, max_score=max_score,
        industry=industry, has_phone=has_phone, has_email=has_email,
        has_website=has_website, validation_status=validation_status,
        city=city,
    )

    result = await db.execute(query)
    rows = result.all()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow(CSV_COLUMNS)

    # Data rows
    for row in rows:
        (
            ls, name, phone, website, city_val, state, country, address,
            latitude, longitude, rating, review_count,
            industry_val, email, description, social_links, founded_year,
            validation_status_val,
        ) = row

        # Determine source from enrichment or validation
        source = "enrichment" if industry_val else "raw_data"

        # Source URL from company website
        source_url = website or ""

        writer.writerow([
            _val(name),
            _val(industry_val),
            _val(address),
            _val(city_val),
            _val(state),
            _val(country),
            _val(phone),
            _val(email),
            _val(website),
            _val(source),
            _val(source_url),
            _val(rating),
            _val(review_count),
            _val(latitude),
            _val(longitude),
            _val(validation_status_val),
            _val(description),
            _val(social_links),
            _val(founded_year),
            _val(ls.industry_score),
            _val(ls.size_score),
            _val(ls.location_score),
            _val(ls.technology_score),
            _val(ls.data_quality_score),
            _val(ls.validation_score),
            _val(ls.total_score),
            _val(ls.score_version),
        ])

    output.seek(0)
    csv_string = output.getvalue()
    record_count = len(rows)

    # Export audit metadata
    audit = {
        "export_time": datetime.now(timezone.utc).isoformat(),
        "format": "csv",
        "record_count": record_count,
        "applied_filters": applied_filters,
        "columns": CSV_COLUMNS,
    }

    logger.info("Level 7: Exported %d records as CSV", record_count)

    return csv_string, record_count, audit
