"""
url: /backend/app/services/enrich_infer.py
About:
  Name-based industry inference and raw_data metadata extraction.
  No external API calls — pure keyword matching and data extraction
  from existing raw_data JSONB fields.
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Industry keyword mapping — ordered by specificity
_INDUSTRY_RULES: list[tuple[str, str]] = [
    # Healthcare — specific
    (r"\beye\s*(?:hospital|care|clinic|center|centre)\b", "Healthcare - Eye Care"),
    (r"\bdental\s*(?:hospital|care|clinic|center|college)\b", "Healthcare - Dental"),
    (r"\borthop[aée]dic\s*(?:hospital|care|clinic)\b", "Healthcare - Orthopedics"),
    (r"\bchild(?:ren)?['']?\s*(?:hospital|care)\b", "Healthcare - Pediatrics"),
    (r"\bmaternity\s*(?:hospital|home|care)\b", "Healthcare - Maternity"),
    (r"\bcancer\s*(?:hospital|care|center)\b", "Healthcare - Oncology"),
    (r"\bheart\s*(?:hospital|care|center)\b", "Healthcare - Cardiology"),
    (r"\bmulti\s*special[ia]ty\s*(?:hospital|care)\b", "Healthcare - Multi Specialty"),
    (r"\bsuper\s*special[ia]ty\s*(?:hospital|care|clinic)\b", "Healthcare - Super Specialty"),
    (r"\bdiagnostic\s*(?:center|centre|lab|labs)\b", "Healthcare - Diagnostics"),
    (r"\bnursing\s*(?:home|college)\b", "Healthcare - Nursing"),
    (r"\bpharmacy|medical\s*store|chemist\b", "Healthcare - Pharmacy"),
    # Healthcare — general
    (r"\bhospital\b", "Healthcare"),
    (r"\bclinic\b", "Healthcare"),
    (r"\bmedical\b", "Healthcare"),
    (r"\bhealth(?:care)?\b", "Healthcare"),
    (r"\bsurgical\b", "Healthcare"),
    (r"\bpathology\b", "Healthcare"),
    (r"\bradiology\b", "Healthcare"),
    (r"\bphysiotherapy\b", "Healthcare"),
    # Education
    (r"\bschool\b", "Education"),
    (r"\bcollege\b", "Education"),
    (r"\buniversity\b", "Education"),
    (r"\bacademy\b", "Education"),
    (r"\binstitute\b", "Education"),
    (r"\beducation\b", "Education"),
    (r"\btraining\b", "Education"),
    # Food & Beverage
    (r"\brestaurant\b", "Food & Beverage"),
    (r"\bfood\s*(?:court|court|point|hub|zone)\b", "Food & Beverage"),
    (r"\bhotel\b", "Hospitality"),
    (r"\bdining\b", "Food & Beverage"),
    (r"\bbakery\b", "Food & Beverage"),
    (r"\bcafe|coffee\b", "Food & Beverage"),
    # Retail
    (r"\bstore\b", "Retail"),
    (r"\bshop\b", "Retail"),
    (r"\bretail\b", "Retail"),
    (r"\bmarket\b", "Retail"),
    (r"\bmall\b", "Retail"),
    # Finance
    (r"\bbank\b", "Finance"),
    (r"\bfinance\b", "Finance"),
    (r"\binsurance\b", "Finance"),
    (r"\binvestment\b", "Finance"),
    (r"\bchartered\s*accountant\b", "Finance"),
    # Technology
    (r"\bsoftware\b", "Technology"),
    (r"\bit\s*(?:solution|service|company)\b", "Technology"),
    (r"\btech(?:nology)?\b", "Technology"),
    (r"\bdigital\b", "Technology"),
    (r"\bcyber\b", "Technology"),
    # Real Estate
    (r"\breal\s*estate\b", "Real Estate"),
    (r"\bproperty\b", "Real Estate"),
    (r"\bconstruction\b", "Construction"),
    # Legal
    (r"\blaw\s*(?:firm|office|associate)\b", "Legal Services"),
    (r"\blegal\b", "Legal Services"),
    (r"\badvocate\b", "Legal Services"),
    # Manufacturing
    (r"\bmanufactur(?:ing|er)\b", "Manufacturing"),
    (r"\bindustri(?:es|al)\b", "Manufacturing"),
    (r"\bfactory\b", "Manufacturing"),
    # Travel
    (r"\btravel\b", "Travel & Tourism"),
    (r"\btour(?:ism)?\b", "Travel & Tourism"),
    (r"\btransport\b", "Transportation & Logistics"),
    (r"\bcourier\b", "Transportation & Logistics"),
    (r"\blogistic\b", "Transportation & Logistics"),
]


def infer_industry_from_name(name: str | None) -> tuple[str | None, str]:
    """Infer industry from company name using keyword matching.

    Returns (industry, source_label) or (None, "") if no match.
    """
    if not name:
        return None, ""

    name_lower = name.lower()
    for pattern, industry in _INDUSTRY_RULES:
        if re.search(pattern, name_lower, re.IGNORECASE):
            return industry, f"inferred_from_name:{name}"

    return None, ""


def extract_from_raw_data(raw_records: list[dict]) -> dict[str, Any]:
    """Extract enrichment data from linked raw_records' raw_data JSONB.

    Extracts:
    - email: from raw_data.email
    - additional_phones: unique phones from all raw records
    - social_links: from raw_data metadata if available
    - google_maps_url: from raw_data.maps_url or metadata
    """
    result: dict[str, Any] = {}
    source_label = "raw_data_metadata"

    emails = set()
    phones = set()
    social_links = {}
    maps_urls = []

    for rr in raw_records:
        raw_data = rr.get("raw_data", {})
        meta = raw_data.get("metadata", {})

        # Email
        email = raw_data.get("email")
        if email and str(email).strip() and "@" in str(email):
            emails.add(str(email).strip().lower())

        # Additional phones
        phone = raw_data.get("phone")
        if phone and str(phone).strip():
            phones.add(str(phone).strip())

        # Maps URL
        maps_url = raw_data.get("maps_url") or meta.get("maps_url")
        if maps_url:
            maps_urls.append(str(maps_url))

        # Social links from metadata (rare but possible)
        if isinstance(meta, dict):
            for key in ["facebook_url", "twitter_url", "linkedin_url", "instagram_url"]:
                val = meta.get(key)
                if val:
                    platform = key.replace("_url", "")
                    social_links[platform] = str(val)

    if emails:
        result["email"] = list(emails)[0]
        result["email_source"] = source_label

    if phones:
        result["additional_phones"] = list(phones)
        result["additional_phones_source"] = source_label

    if social_links:
        result["social_links"] = social_links
        result["social_links_source"] = source_label

    if maps_urls:
        result["google_maps_url"] = maps_urls[0]

    result["source"] = source_label
    return result
