"""
url: /backend/app/services/level3.py
About:
  Level 3 CLEAN pipeline orchestrator. Reads raw_records from Level 2,
  applies cleaning/standardization, performs entity resolution to identify
  duplicates, and creates Company records as the cleaned representation.

  This service is idempotent — it can be re-run without duplicating
  Company records. It clears previous Level 3 data for the organization
  before re-processing.

  Level 3 does NOT:
  - Delete or modify raw_records
  - Call external APIs
  - Perform validation (Level 4)
  - Perform enrichment (Level 5)
  - Perform scoring/filtering (Level 6)
"""

import logging
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.raw_record import RawRecord
from app.services.clean import clean_raw_data
from app.services.entity_resolution import resolve_entities

logger = logging.getLogger(__name__)


def _detect_country(cluster) -> str:
    """Detect country from cluster data (phone, address, city, state).
    
    Uses phone prefix and known location data to determine country.
    Falls back to 'Unknown' when country cannot be determined.
    """
    phone = (cluster.best_phone or "").strip()
    city = (cluster.best_city or "").lower()
    state = (cluster.best_state or "").lower()
    address = (cluster.best_address or "").lower()

    # Phone prefix detection
    if phone.startswith("+91") or phone.startswith("91"):
        return "India"
    if phone.startswith("+44"):
        return "United Kingdom"
    if phone.startswith("+1"):
        return "United States"
    if phone.startswith("+61"):
        return "Australia"
    if phone.startswith("+81"):
        return "Japan"
    if phone.startswith("+49"):
        return "Germany"
    if phone.startswith("+33"):
        return "France"
    if phone.startswith("+55"):
        return "Brazil"
    if phone.startswith("+52"):
        return "Mexico"
    if phone.startswith("+86"):
        return "China"
    if phone.startswith("+971"):
        return "UAE"
    if phone.startswith("+65"):
        return "Singapore"
    if phone.startswith("+82"):
        return "South Korea"
    if phone.startswith("+39"):
        return "Italy"
    if phone.startswith("+34"):
        return "Spain"
    if phone.startswith("+31"):
        return "Netherlands"
    if phone.startswith("+46"):
        return "Sweden"

    # Indian states in address
    indian_states = {
        "andhra pradesh", "arunachal pradesh", "assam", "bihar",
        "chhattisgarh", "goa", "gujarat", "haryana", "himachal pradesh",
        "jharkhand", "karnataka", "kerala", "madhya pradesh", "maharashtra",
        "manipur", "meghalaya", "mizoram", "nagaland", "odisha", "punjab",
        "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura",
        "uttar pradesh", "uttarakhand", "west bengal", "delhi",
    }
    if state in indian_states or city in indian_states:
        return "India"

    # UK cities
    uk_cities = {"london", "manchester", "birmingham", "leeds", "glasgow",
                 "edinburgh", "liverpool", "bristol", "cardiff", "belfast"}
    if city in uk_cities:
        return "United Kingdom"

    # US cities
    us_cities = {"new york", "los angeles", "chicago", "houston", "phoenix",
                 "san francisco", "seattle", "boston", "miami", "dallas"}
    if city in us_cities:
        return "United States"

    # Canadian cities
    ca_cities = {"toronto", "vancouver", "montreal", "calgary", "ottawa"}
    if city in ca_cities:
        return "Canada"

    return "Unknown"


async def run_clean(
    db: AsyncSession,
    organization_id,
    pipeline_run_id=None,
) -> dict:
    """Execute Level 3 CLEAN pipeline.

    1. Read all raw_records for the organization (optionally filtered by pipeline_run_id)
    2. Clean/standardize each record
    3. Resolve entities (identify duplicates)
    4. Create/update Company records
    5. Link raw_records to their Company via company_id FK

    Returns a summary dict with counts.
    """
    # --- Step 1: Read raw records ---
    query = select(RawRecord).where(RawRecord.organization_id == organization_id)
    if pipeline_run_id:
        query = query.where(RawRecord.pipeline_run_id == pipeline_run_id)

    result = await db.execute(query)
    raw_records = list(result.scalars().all())

    if not raw_records:
        logger.info("No raw records found for organization %s", organization_id)
        return {
            "raw_records_read": 0,
            "raw_records_processed": 0,
            "companies_created": 0,
            "duplicates_identified": 0,
            "records_with_changes": 0,
            "records_without_changes": 0,
        }

    logger.info("Level 3: Read %d raw records for organization %s",
                len(raw_records), organization_id)

    # --- Step 2: Clean each record ---
    cleaned_records = []
    records_with_changes = 0
    records_without_changes = 0

    for rr in raw_records:
        raw_data = rr.raw_data or {}
        cleaned = clean_raw_data(raw_data)

        # Attach tracking metadata (not stored in raw_data)
        cleaned["_raw_record_id"] = str(rr.id)
        cleaned["_source_adapter"] = rr.source_adapter
        cleaned["_source_record_id"] = rr.source_record_id or ""

        changes = cleaned.get("_level3_changes", [])
        if changes:
            records_with_changes += 1
        else:
            records_without_changes += 1

        cleaned_records.append(cleaned)

    logger.info("Level 3: Cleaned %d records (%d with changes, %d unchanged)",
                len(cleaned_records), records_with_changes, records_without_changes)

    # --- Step 3: Resolve entities ---
    clusters = resolve_entities(cleaned_records)

    logger.info("Level 3: Resolved %d entities from %d raw records",
                len(clusters), len(cleaned_records))

    # Count duplicates
    duplicates_identified = sum(len(c.duplicate_of) for c in clusters)

    # --- Step 4: No longer delete all companies per search ---
    # Each search adds new companies; entity resolution handles dedup.
    # This preserves results across multiple searches for maximum lead discovery.

    # --- Step 5: Create or update Company records and link raw_records ---
    companies_created = 0

    # Build lookup of existing companies by normalized name for dedup
    existing_companies_result = await db.execute(
        select(Company).where(Company.organization_id == organization_id)
    )
    existing_companies = {c.name.lower().strip(): c for c in existing_companies_result.scalars().all()}

    for cluster in clusters:
        company_name = (cluster.best_name or "Unknown").strip()
        company_name_lower = company_name.lower()

        # Check if company already exists (dedup by name)
        existing = existing_companies.get(company_name_lower)
        if existing:
            company = existing
            # Update fields if new data is better
            if cluster.best_phone and not company.phone:
                company.phone = cluster.best_phone
                company.phone_intl = cluster.best_phone
            if cluster.best_website and not company.website:
                company.website = cluster.best_website
            if cluster.best_address and not company.address:
                company.address = cluster.best_address
            if cluster.best_city and not company.city:
                company.city = cluster.best_city
            if cluster.best_state and not company.state:
                company.state = cluster.best_state
            if cluster.latitude and not company.latitude:
                company.latitude = Decimal(str(cluster.latitude))
            if cluster.longitude and not company.longitude:
                company.longitude = Decimal(str(cluster.longitude))
            if cluster.rating and not company.rating:
                company.rating = Decimal(str(cluster.rating))
            if cluster.review_count and not company.review_count:
                company.review_count = cluster.review_count
        else:
            company = Company(
                id=uuid4(),
                organization_id=organization_id,
                name=company_name,
                domain=_extract_domain(cluster.best_website),
                industry=None,
                categories=None,
                address=cluster.best_address,
                city=cluster.best_city,
                state=cluster.best_state,
                country=_detect_country(cluster),
                latitude=Decimal(str(cluster.latitude)) if cluster.latitude else None,
                longitude=Decimal(str(cluster.longitude)) if cluster.longitude else None,
                phone=cluster.best_phone,
                phone_intl=cluster.best_phone,
                website=cluster.best_website,
                rating=Decimal(str(cluster.rating)) if cluster.rating else None,
                review_count=cluster.review_count,
                business_status=None,
                google_maps_url=None,
                source_place_id=None,
                source_cin=None,
                completeness_score=Decimal(str(cluster.completeness_score)),
            )
            db.add(company)
            existing_companies[company_name_lower] = company
            companies_created += 1

        # Link raw_records to this company
        for rr_id in cluster.raw_record_ids:
            if rr_id:
                await db.execute(
                    RawRecord.__table__.update()
                    .where(RawRecord.id == rr_id)
                    .values(company_id=company.id)
                )

    # --- Step 6: Store cleaned data in normalized_data column ---
    # Build a lookup from raw_record_id to cleaned data
    cleaned_lookup = {
        cr["_raw_record_id"]: cr for cr in cleaned_records
    }

    for rr in raw_records:
        rr_id_str = str(rr.id)
        if rr_id_str in cleaned_lookup:
            cleaned = cleaned_lookup[rr_id_str]
            # Remove internal tracking keys before storing
            store_data = {
                k: v for k, v in cleaned.items()
                if not k.startswith("_")
            }
            rr.normalized_data = store_data
            rr.status = "cleaned"

    await db.commit()

    logger.info("Level 3: Created %d companies, linked %d raw records",
                companies_created, sum(len(c.raw_record_ids) for c in clusters))

    return {
        "raw_records_read": len(raw_records),
        "raw_records_processed": len(cleaned_records),
        "companies_created": companies_created,
        "duplicates_identified": duplicates_identified,
        "records_with_changes": records_with_changes,
        "records_without_changes": records_without_changes,
        "raw_records_untouched": 0,  # raw_data field is never modified
        "clusters_with_multiple": sum(1 for c in clusters if len(c.raw_record_ids) > 1),
        "clusters_single": sum(1 for c in clusters if len(c.raw_record_ids) == 1),
    }


def _extract_domain(url: str | None) -> str | None:
    """Extract domain from a URL for the companies.domain field."""
    if not url:
        return None
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.lower() if domain else None
    except Exception:
        return None
