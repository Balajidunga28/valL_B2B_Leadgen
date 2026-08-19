"""
url: /backend/app/services/score.py
About:
  Level 6 scoring logic. Transparent, deterministic scoring system
  with documented weights and formulas. Each factor produces a score
  from 0.0 to 1.0. Missing data is handled explicitly — not assumed
  positive.

SCORING FORMULA (version 1.0):
========================================

  total_score = industry_score     * 0.20
              + size_score         * 0.10
              + location_score     * 0.15
              + technology_score   * 0.10
              + data_quality_score * 0.25
              + validation_score   * 0.20

  Each factor: 0.0 to 1.0
  Total score: 0 to 100

FACTOR DEFINITIONS:
========================================

  industry_score (weight: 0.20):
    1.0  = industry is set and is a recognized healthcare/known category
    0.5  = industry is set but unrecognized/generic
    0.0  = industry is NOT_AVAILABLE (null)

  size_score (weight: 0.10):
    1.0  = company_size is available
    0.0  = company_size is NOT_AVAILABLE (null)

  location_score (weight: 0.15):
    1.0  = both city and coordinates are available
    0.7  = city is available but no coordinates
    0.5  = coordinates available but no city name
    0.3  = address is available but no city/coordinates
    0.0  = no location data

  technology_score (weight: 0.10):
    1.0  = technologies list is available
    0.0  = technologies NOT_AVAILABLE (null)

  data_quality_score (weight: 0.25):
    Completeness of key business fields:
    - phone, website, email, address, description, social_links, rating, reviews
    Score = fields_present / total_fields

  validation_score (weight: 0.20):
    1.0  = overall validation status is VALID
    0.5  = overall validation status is UNKNOWN
    0.0  = overall validation status is INVALID

SCORING TIERS:
  High:   >= 60
  Medium: >= 35 and < 60
  Low:    < 35
"""

import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

# --- Scoring weights ---
SCORE_VERSION = "1.0"
WEIGHTS = {
    "industry": Decimal("0.20"),
    "size": Decimal("0.10"),
    "location": Decimal("0.15"),
    "technology": Decimal("0.10"),
    "data_quality": Decimal("0.25"),
    "validation": Decimal("0.20"),
}

# Recognized industries (higher score)
_RECOGNIZED_INDUSTRIES = {
    "healthcare", "education", "finance", "technology", "retail",
    "manufacturing", "real estate", "legal services", "hospitality",
    "food & beverage", "travel & tourism", "construction",
    "transportation & logistics", "accounting",
}

# Industries with sub-categories (e.g., "Healthcare - Eye Care")
_HEALTHCARE_SUBS = {
    "healthcare - eye care", "healthcare - dental", "healthcare - orthopedics",
    "healthcare - pediatrics", "healthcare - maternity", "healthcare - oncology",
    "healthcare - cardiology", "healthcare - multi specialty",
    "healthcare - super specialty", "healthcare - diagnostics",
    "healthcare - nursing", "healthcare - pharmacy",
}


def score_industry(industry: str | None) -> Decimal:
    """Score based on whether industry is available and recognized.
    
    Returns 0.5 when industry is unknown — the business is still real,
    we just haven't classified it. Only returns 0.0 when explicitly
    set to an invalid value.
    """
    if not industry:
        return Decimal("0.5")

    industry_lower = industry.lower().strip()

    # Recognized specific industry (including sub-categories)
    if industry_lower in _HEALTHCARE_SUBS or industry_lower in _RECOGNIZED_INDUSTRIES:
        return Decimal("1.0")

    # Partially recognized (starts with a known industry)
    for known in _RECOGNIZED_INDUSTRIES:
        if industry_lower.startswith(known):
            return Decimal("1.0")

    # Industry is set but unrecognized — still a real business
    return Decimal("0.7")


def score_size(company_size: str | None) -> Decimal:
    """Score based on whether company size information is available.
    
    Returns 0.5 when unknown — missing size data doesn't mean the
    business isn't real.
    """
    if company_size and str(company_size).strip():
        return Decimal("1.0")
    return Decimal("0.5")


def score_location(
    city: str | None,
    latitude: Decimal | float | None,
    longitude: Decimal | float | None,
    address: str | None,
) -> Decimal:
    """Score based on location data availability."""
    has_city = bool(city and str(city).strip())
    has_coords = bool(latitude is not None and longitude is not None)
    has_address = bool(address and str(address).strip())

    if has_city and has_coords:
        return Decimal("1.0")
    if has_city:
        return Decimal("0.7")
    if has_coords:
        return Decimal("0.5")
    if has_address:
        return Decimal("0.3")
    return Decimal("0.0")


def score_technology(technologies: list | None) -> Decimal:
    """Score based on whether technology information is available.
    
    Returns 0.5 when unknown — missing tech data doesn't mean the
    business isn't real.
    """
    if technologies and isinstance(technologies, list) and len(technologies) > 0:
        return Decimal("1.0")
    return Decimal("0.5")


def score_data_quality(
    phone: str | None,
    website: str | None,
    email: str | None,
    address: str | None,
    description: str | None,
    social_links: dict | None,
    rating: Decimal | float | None,
    review_count: int | None,
) -> Decimal:
    """Score based on completeness of key business fields.

    Score = fields_present / total_fields
    """
    fields = [
        bool(phone),
        bool(website),
        bool(email),
        bool(address),
        bool(description),
        bool(social_links),
        rating is not None,
        review_count is not None,
    ]
    present = sum(1 for f in fields if f)
    return Decimal(str(round(present / len(fields), 2)))


def score_validation(overall_status: str | None) -> Decimal:
    """Score based on Level 4 validation status."""
    if overall_status == "VALID":
        return Decimal("1.0")
    if overall_status == "UNKNOWN":
        return Decimal("0.5")
    if overall_status == "INVALID":
        return Decimal("0.0")
    return Decimal("0.0")


def compute_total_score(
    industry_score: Decimal,
    size_score: Decimal,
    location_score: Decimal,
    technology_score: Decimal,
    data_quality_score: Decimal,
    validation_score: Decimal,
) -> Decimal:
    """Compute total score from weighted factor scores.

    total = sum(factor * weight) * 100
    """
    total = (
        industry_score * WEIGHTS["industry"] +
        size_score * WEIGHTS["size"] +
        location_score * WEIGHTS["location"] +
        technology_score * WEIGHTS["technology"] +
        data_quality_score * WEIGHTS["data_quality"] +
        validation_score * WEIGHTS["validation"]
    )
    return Decimal(str(round(float(total) * 100, 2)))


def score_company(
    company_data: dict[str, Any],
    enrichment_data: dict[str, Any],
    validation_data: dict[str, Any],
) -> dict[str, Any]:
    """Score a single company. Returns a dict with all factor scores and total.

    Args:
        company_data: From companies table (phone, website, city, etc.)
        enrichment_data: From company_enrichments table (industry, size, etc.)
        validation_data: From company_validations table (overall_status)

    Returns:
        Dict with industry_score, size_score, location_score, technology_score,
        data_quality_score, validation_score, total_score.
    """
    ind = score_industry(enrichment_data.get("industry"))
    sz = score_size(enrichment_data.get("company_size"))
    loc = score_location(
        company_data.get("city"),
        company_data.get("latitude"),
        company_data.get("longitude"),
        company_data.get("address"),
    )
    tech = score_technology(enrichment_data.get("technologies"))
    dq = score_data_quality(
        company_data.get("phone"),
        company_data.get("website"),
        enrichment_data.get("email"),
        company_data.get("address"),
        enrichment_data.get("description"),
        enrichment_data.get("social_links"),
        company_data.get("rating"),
        company_data.get("review_count"),
    )
    val = score_validation(validation_data.get("overall_status"))

    total = compute_total_score(ind, sz, loc, tech, dq, val)

    return {
        "industry_score": ind,
        "size_score": sz,
        "location_score": loc,
        "technology_score": tech,
        "data_quality_score": dq,
        "validation_score": val,
        "total_score": total,
        "score_version": SCORE_VERSION,
        "scoring_formula": {
            "version": SCORE_VERSION,
            "weights": {k: float(v) for k, v in WEIGHTS.items()},
            "formula": "total = sum(factor * weight) * 100",
        },
    }
