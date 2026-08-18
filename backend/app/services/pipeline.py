"""
url: /backend/app/services/pipeline.py
About:
  Pipeline service for ValLG. Orchestrates multi-source extraction concurrently,
  performs cross-source deduplication and entity resolution, merges complementary
  fields with provenance tracking, validates location, and stores canonical leads.
  Fully generic — uses shared geo_config for all geographic/category data.
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.google_places import GooglePlacesAdapter
from app.adapters.google_search import GoogleSearchAdapter
from app.adapters.openstreetmap import OpenStreetMapAdapter
from app.adapters.web_search import WebSearchAdapter
from app.adapters.indiamart import IndiaMARTAdapter
from app.adapters.justdial import JustDialAdapter
from app.geo import (
    CITY_COORDS,
    GENERIC_BUSINESS_SUFFIXES,
    GENERIC_SKIP_WORDS,
    LOCATION_MATCH_RADIUS_DEGREES,
    ENTITY_MATCH_RADIUS_DEGREES,
    get_coords_for_city,
)
from app.models.pipeline_run import PipelineRun
from app.models.raw_record import RawRecord
from app.models.source_api_key import SourceApiKey

logger = logging.getLogger(__name__)

ADAPTERS = {
    "google_places": GooglePlacesAdapter,
    "google_search": GoogleSearchAdapter,
    "openstreetmap": OpenStreetMapAdapter,
    "web_search": WebSearchAdapter,
    "indiamart": IndiaMARTAdapter,
    "justdial": JustDialAdapter,
}

FREE_SOURCES = {"openstreetmap", "google_search", "web_search", "indiamart", "justdial"}


async def get_adapter(db: AsyncSession, organization_id, source_name: str):
    if source_name not in ADAPTERS:
        raise ValueError(f"Unknown source: {source_name}")
    adapter_class = ADAPTERS[source_name]
    if source_name in FREE_SOURCES:
        return adapter_class()
    result = await db.execute(
        select(SourceApiKey).where(
            SourceApiKey.organization_id == organization_id,
            SourceApiKey.source_adapter == source_name,
            SourceApiKey.status == "active",
        )
    )
    api_key_record = result.scalar_one_or_none()
    if api_key_record is None:
        raise ValueError(f"No active API key for source: {source_name}")
    return adapter_class(api_key=api_key_record.api_key_encrypted)


def _normalize_phone(phone: str | None) -> str:
    if not phone:
        return ""
    p = re.sub(r"[^0-9]", "", phone)
    if p.startswith("91") and len(p) > 10:
        p = p[2:]
    return p


def _normalize_name(name: str) -> str:
    n = name.lower().strip()
    n = re.sub(r"[^a-z0-9]", "", n)
    for s in GENERIC_BUSINESS_SUFFIXES:
        if n.endswith(s):
            n = n[:-len(s)]
            break
    return n


def _entity_key(record: dict) -> str:
    raw = record.get("raw_data", {})
    name = _normalize_name(raw.get("name") or "")
    phone = _normalize_phone(raw.get("phone"))
    website = (raw.get("website") or "").lower().strip()
    domain = ""
    if website:
        m = re.search(r"https?://(?:www\.)?([^/]+)", website)
        if m:
            domain = re.sub(r"[^a-z0-9]", "", m.group(1))

    if phone and len(phone) >= 8:
        return f"phone:{phone}"
    if name and domain:
        return f"name:{name}|domain:{domain}"
    if name:
        return f"name:{name}"
    return hashlib.md5(str(raw).encode()).hexdigest()


def _are_same_entity(a: dict, b: dict) -> bool:
    """Determine if two records represent the same business entity."""
    raw_a = a.get("raw_data", {})
    raw_b = b.get("raw_data", {})

    phone_a = _normalize_phone(raw_a.get("phone"))
    phone_b = _normalize_phone(raw_b.get("phone"))
    if phone_a and phone_b and phone_a == phone_b:
        return True

    name_a = _normalize_name(raw_a.get("name") or "")
    name_b = _normalize_name(raw_b.get("name") or "")
    if name_a and name_b and (name_a == name_b or name_a in name_b or name_b in name_a):
        return True

    website_a = (raw_a.get("website") or "").lower()
    website_b = (raw_b.get("website") or "").lower()
    if website_a and website_b:
        domain_a = re.sub(r"[^a-z0-9]", "", re.search(r"https?://(?:www\.)?([^/]+)", website_a or "").group(1) if re.search(r"https?://(?:www\.)?([^/]+)", website_a) else "")
        domain_b = re.sub(r"[^a-z0-9]", "", re.search(r"https?://(?:www\.)?([^/]+)", website_b or "").group(1) if re.search(r"https?://(?:www\.)?([^/]+)", website_b) else "")
        if domain_a and domain_b and domain_a == domain_b:
            return True

    lat_a = raw_a.get("latitude")
    lng_a = raw_a.get("longitude")
    lat_b = raw_b.get("latitude")
    lng_b = raw_b.get("longitude")
    if lat_a and lng_a and lat_b and lng_b:
        dist = ((lat_a - lat_b) ** 2 + (lng_a - lng_b) ** 2) ** 0.5
        if dist < ENTITY_MATCH_RADIUS_DEGREES:
            if name_a and name_b and len(set(name_a) & set(name_b)) / max(len(set(name_a)), 1) > 0.5:
                return True

    return False


def _merge_records(records: list[dict]) -> dict:
    merged = {}
    source_list = set()
    field_sources: dict[str, list[str]] = {}

    priority_fields = ["name", "address", "phone", "website", "email",
                       "industry", "rating", "reviews_count", "opening_hours",
                       "latitude", "longitude", "city", "state", "pin_code",
                       "maps_url", "source_url"]

    for rec in records:
        raw = rec.get("raw_data", {})
        src = raw.get("metadata", {}).get("extraction_method") or rec.get("source_adapter", "unknown")
        source_list.add(src)

        for field in priority_fields:
            val = raw.get(field)
            if val is not None and val != "" and val != 0:
                if not merged.get(field):
                    merged[field] = val
                    field_sources[field] = [src]
                elif field == "rating" and isinstance(val, (int, float)):
                    existing = merged.get(field)
                    if existing is None or val > existing:
                        merged[field] = val
                        field_sources[field] = [src]
                elif field == "reviews_count" and isinstance(val, int):
                    existing = merged.get(field, 0) or 0
                    if val > existing:
                        merged[field] = val
                        field_sources[field] = [src]
                elif field not in merged:
                    merged[field] = val
                    field_sources[field] = [src]

    merged["sources"] = sorted(source_list)
    merged["field_sources"] = field_sources
    return merged


def _validate_location(record: dict, city: str | None, state: str | None) -> bool:
    if not city and not state:
        return True

    raw = record.get("raw_data", {})
    text = " ".join([
        raw.get("address") or "",
        raw.get("city") or "",
        raw.get("state") or "",
        raw.get("name") or "",
    ]).lower()

    lat = raw.get("latitude")
    lng = raw.get("longitude")

    city_lower = (city or "").lower().strip()
    state_lower = (state or "").lower().strip()

    if city_lower:
        if city_lower in text:
            return True

        if state_lower and state_lower in text:
            return True

        if lat and lng:
            coords = get_coords_for_city(city_lower)
            if coords:
                clat, clng = coords
                dist = ((lat - clat) ** 2 + (lng - clng) ** 2) ** 0.5
                if dist < LOCATION_MATCH_RADIUS_DEGREES:
                    return True

        return False

    if state_lower:
        return state_lower in text
    return False


def _estimate_completeness(lead: dict) -> float:
    fields = ["name", "phone", "address", "website", "email", "industry",
              "rating", "reviews_count", "latitude", "longitude", "maps_url",
              "opening_hours", "city", "state", "pin_code"]
    present = sum(1 for f in fields if lead.get(f) is not None and lead.get(f) != "")
    return round(present / len(fields) * 100, 1)


async def _extract_from_source(source_name: str, adapter, query: str, location: str | None, limit: int) -> tuple[str, list[dict], str | None]:
    try:
        raw_records = await adapter.search(query=query, location=location, limit=limit)
        normalized = []
        for rec in raw_records:
            n = adapter.normalize(rec)
            n["_source_adapter"] = source_name
            normalized.append(n)
        await adapter.close()
        return source_name, normalized, None
    except ValueError as e:
        await adapter.close()
        return source_name, [], str(e)
    except Exception as e:
        logger.error(f"Error from {source_name}: {e}")
        try:
            await adapter.close()
        except Exception:
            pass
        return source_name, [], str(e)


async def run_extraction(
    db: AsyncSession,
    organization_id,
    user_id,
    query: str,
    location: str | None,
    sources: list[str],
    limit: int,
) -> PipelineRun:
    run = PipelineRun(
        id=uuid4(),
        organization_id=organization_id,
        user_id=user_id,
        query_text=query,
        query_params={
            "query": query,
            "location": location,
            "sources": sources,
            "limit": limit,
        },
        status="running",
        sources_used=sources,
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    adapters = {}
    for source_name in sources:
        try:
            adapters[source_name] = await get_adapter(db, organization_id, source_name)
        except ValueError as e:
            logger.warning(f"Source {source_name} not available: {e}")

    extraction_limit = max(limit, 200)

    tasks = [
        _extract_from_source(name, adapters[name], query, location, extraction_limit)
        for name in adapters
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    source_counts: dict[str, int] = {}
    errors = []
    source_warnings = []

    for result in results:
        if isinstance(result, Exception):
            errors.append(str(result))
            continue
        source_name, records, error = result
        source_counts[source_name] = len(records)
        if error:
            if "No active API key" in error or "Unknown source" in error:
                source_warnings.append(f"{source_name}: {error}")
            else:
                errors.append(f"{source_name}: {error}")

    logger.info(f"Raw records per source: {source_counts}")

    city = None
    state = None
    if location:
        parts = [p.strip() for p in location.split(",")]
        city = parts[0] if parts else None
        state = parts[1].strip() if len(parts) > 1 else None

    stored_count = 0
    for result in results:
        if isinstance(result, Exception):
            continue
        source_name, normalized_records, error = result

        for rec in normalized_records:
            raw_data = rec.get("raw_data", {})
            source_adapter = rec.get("_source_adapter", source_name)

            # Filter out records that don't match the requested location
            if not _validate_location(rec, city, state):
                continue

            raw_data.setdefault("metadata", {})
            raw_data["metadata"]["extraction_method"] = source_adapter
            raw_data["metadata"]["contributing_sources"] = [source_adapter]
            raw_data["metadata"]["completeness_score"] = _estimate_completeness(raw_data)

            record = RawRecord(
                id=uuid4(),
                organization_id=organization_id,
                pipeline_run_id=run.id,
                source_adapter=source_adapter,
                source_record_id=rec.get("source_record_id", f"rec_{hashlib.md5(str(raw_data.get('name', '')).encode()).hexdigest()[:12]}"),
                raw_data=raw_data,
                status="extracted",
                retrieved_at=datetime.now(timezone.utc),
            )
            db.add(record)
            stored_count += 1

    run.total_extracted = stored_count
    if stored_count > 0:
        run.status = "completed"
    elif errors:
        run.status = "failed"
    else:
        run.status = "completed"

    run.error_message = "; ".join(source_warnings + errors) if (source_warnings or errors) else None
    run.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(run)

    logger.info(f"Pipeline run {run.id}: {stored_count} records stored from sources: {source_counts}")

    return run


async def get_pipeline_run(db: AsyncSession, run_id, organization_id):
    result = await db.execute(
        select(PipelineRun).where(
            PipelineRun.id == run_id,
            PipelineRun.organization_id == organization_id,
        )
    )
    return result.scalar_one_or_none()


async def get_raw_records(db: AsyncSession, pipeline_run_id, organization_id):
    result = await db.execute(
        select(RawRecord).where(
            RawRecord.pipeline_run_id == pipeline_run_id,
            RawRecord.organization_id == organization_id,
        )
    )
    return list(result.scalars().all())
