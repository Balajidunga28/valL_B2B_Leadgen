"""
url: /backend/app/services/level5.py
About:
  Level 5 ENRICH pipeline orchestrator. Reads validated Company records
  from Level 3/4 and enriches them with additional data from:
  - Website scraping (companies with websites)
  - Name-based industry inference (all companies)
  - Raw data metadata extraction (all companies)

  Level 5 does NOT:
  - Modify raw_records (Level 2)
  - Modify companies (Level 3)
  - Modify company_validations (Level 4)
  - Score or filter leads (Level 6)
  - Export data (Level 7)
"""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_enrichment import CompanyEnrichment
from app.models.raw_record import RawRecord
from app.services.enrich_website import scrape_website
from app.services.enrich_infer import infer_industry_from_name, extract_from_raw_data

logger = logging.getLogger(__name__)

_SCRAPE_SEMAPHORE = asyncio.Semaphore(5)


def _merge_enrichment(
    base: dict,
    website_data: dict,
    infer_data: dict,
    metadata_data: dict,
) -> dict:
    """Merge enrichment data from multiple sources.

    Priority: website > name inference > metadata
    Each field retains the source of the winning value.
    """
    merged = {}

    # Industry: prefer website, then inference
    merged["industry"] = website_data.get("industry") or infer_data.get("industry")
    merged["industry_source"] = (
        website_data.get("industry_source") or infer_data.get("industry_source") or ""
    )

    # Company size: website only
    merged["company_size"] = website_data.get("company_size")
    merged["company_size_source"] = website_data.get("company_size_source", "")

    # Revenue: not available from these sources
    merged["revenue_range"] = None
    merged["revenue_range_source"] = ""

    # Founded year: website only
    merged["founded_year"] = website_data.get("founded_year")
    merged["founded_year_source"] = website_data.get("founded_year_source", "")

    # Description: prefer website meta description
    merged["description"] = website_data.get("description")
    merged["description_source"] = website_data.get("source", "")

    # Social links: merge from website and metadata
    social = {}
    if metadata_data.get("social_links"):
        social.update(metadata_data["social_links"])
    if website_data.get("social_links"):
        social.update(website_data["social_links"])
    merged["social_links"] = social if social else None
    merged["social_links_source"] = (
        website_data.get("social_links_source") or metadata_data.get("social_links_source") or ""
    )

    # Technologies: not available from these sources
    merged["technologies"] = None
    merged["technologies_source"] = ""

    # Email: prefer website, then metadata
    merged["email"] = website_data.get("email") or metadata_data.get("email")
    merged["email_source"] = (
        website_data.get("email_source") or metadata_data.get("email_source") or ""
    )

    # Additional phones: metadata only
    merged["additional_phones"] = metadata_data.get("additional_phones")
    merged["additional_phones_source"] = metadata_data.get("additional_phones_source", "")

    # Google Maps URL
    merged["google_maps_url"] = metadata_data.get("google_maps_url")

    return merged


async def run_enrich(
    db: AsyncSession,
    organization_id,
) -> dict:
    """Execute Level 5 ENRICH pipeline.

    1. Read all companies for the organization
    2. For each company, load linked raw_records
    3. Enrich via: website scraping, name inference, metadata extraction
    4. Store results in company_enrichments table

    Returns a summary dict with counts.
    """
    # --- Step 1: Read all companies ---
    result = await db.execute(
        select(Company).where(Company.organization_id == organization_id)
    )
    companies = list(result.scalars().all())

    if not companies:
        logger.info("Level 5: No companies found for organization %s", organization_id)
        return {
            "companies_read": 0,
            "enriched": 0,
            "with_website_scrape": 0,
            "with_industry_inference": 0,
            "with_metadata_extraction": 0,
            "errors": 0,
        }

    logger.info("Level 5: Enriching %d companies for organization %s",
                len(companies), organization_id)

    # --- Step 2: Clear previous enrichment ---
    await db.execute(
        delete(CompanyEnrichment).where(
            CompanyEnrichment.organization_id == organization_id
        )
    )
    await db.flush()

    # --- Step 3: Parallel website scraping for all companies ---
    async def _scrape_one(company):
        if not company.website:
            return company.id, {}
        try:
            async with _SCRAPE_SEMAPHORE:
                data = await scrape_website(company.website)
                if "error" not in data:
                    return company.id, data
                return company.id, {}
        except Exception as e:
            logger.warning("Website scrape error for %s: %s", company.name, e)
            return company.id, {}

    scrape_tasks = [_scrape_one(c) for c in companies]
    scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)
    website_data_map = {}
    scrape_errors = 0
    scrape_success = 0
    for res in scrape_results:
        if isinstance(res, Exception):
            scrape_errors += 1
            continue
        cid, data = res
        website_data_map[cid] = data
        if data:
            scrape_success += 1

    # --- Step 4: Enrich each company (fast, local-only) ---
    stats = {
        "enriched": 0,
        "with_website_scrape": scrape_success,
        "with_industry_inference": 0,
        "with_metadata_extraction": 0,
        "with_social_links": 0,
        "with_email": 0,
        "with_founded_year": 0,
        "with_company_size": 0,
        "with_description": 0,
        "errors": scrape_errors,
    }

    for company in companies:
        # Load raw_records for this company
        raw_records_data = []
        if company.raw_records:
            for rr in company.raw_records:
                raw_records_data.append({
                    "id": str(rr.id),
                    "source_adapter": rr.source_adapter,
                    "raw_data": rr.raw_data or {},
                })

        # --- Source A: Website scraping (from parallel results) ---
        website_data = website_data_map.get(company.id, {})

        # --- Source B: Name-based industry inference ---
        infer_industry, infer_source = infer_industry_from_name(company.name)
        infer_data = {}
        if infer_industry:
            infer_data = {
                "industry": infer_industry,
                "industry_source": infer_source,
            }
            stats["with_industry_inference"] += 1

        # --- Source C: Raw data metadata extraction ---
        metadata_data = extract_from_raw_data(raw_records_data)
        if metadata_data.get("email") or metadata_data.get("additional_phones") or metadata_data.get("social_links"):
            stats["with_metadata_extraction"] += 1

        # --- Merge enrichment data ---
        merged = _merge_enrichment({}, website_data, infer_data, metadata_data)

        # --- Create enrichment record ---
        enrichment = CompanyEnrichment(
            id=uuid4(),
            organization_id=organization_id,
            company_id=company.id,
            industry=merged.get("industry"),
            industry_source=merged.get("industry_source") or None,
            company_size=merged.get("company_size"),
            company_size_source=merged.get("company_size_source") or None,
            revenue_range=merged.get("revenue_range"),
            revenue_range_source=merged.get("revenue_range_source") or None,
            founded_year=merged.get("founded_year"),
            founded_year_source=merged.get("founded_year_source") or None,
            description=merged.get("description"),
            description_source=merged.get("description_source") or None,
            social_links=merged.get("social_links"),
            social_links_source=merged.get("social_links_source") or None,
            technologies=merged.get("technologies"),
            technologies_source=merged.get("technologies_source") or None,
            email=merged.get("email"),
            email_source=merged.get("email_source") or None,
            additional_phones=merged.get("additional_phones"),
            additional_phones_source=merged.get("additional_phones_source") or None,
            enrichment_data={
                "website_data": {k: v for k, v in website_data.items() if k != "error"},
                "infer_data": infer_data,
                "metadata_data": {k: v for k, v in metadata_data.items()
                                  if k not in ("source", "google_maps_url")},
                "raw_records_count": len(raw_records_data),
            },
            enriched_at=datetime.now(timezone.utc),
        )
        db.add(enrichment)
        stats["enriched"] += 1

        # Update sub-stats
        if merged.get("social_links"):
            stats["with_social_links"] += 1
        if merged.get("email"):
            stats["with_email"] += 1
        if merged.get("founded_year"):
            stats["with_founded_year"] += 1
        if merged.get("company_size"):
            stats["with_company_size"] += 1
        if merged.get("description"):
            stats["with_description"] += 1

    await db.commit()

    logger.info("Level 5: Enriched %d companies — website_scrape=%d, inference=%d, metadata=%d",
                stats["enriched"], stats["with_website_scrape"],
                stats["with_industry_inference"], stats["with_metadata_extraction"])

    return {
        "companies_read": len(companies),
        **stats,
    }
