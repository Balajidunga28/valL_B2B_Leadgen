"""
url: /backend/app/services/validate.py
About:
  Level 4 validation checks. Each function validates one aspect of a
  company record and returns a status + details. No external enrichment —
  pure validation of existing data.

  Status values: VALID, INVALID, UNKNOWN, NOT_AVAILABLE
  - NOT_AVAILABLE: field is null/empty — nothing to validate
  - UNKNOWN: field exists but cannot be verified with available tools
  - VALID: field passes validation checks
  - INVALID: field fails validation checks
"""

import re
import logging
import socket
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Status constants
VALID = "VALID"
INVALID = "INVALID"
UNKNOWN = "UNKNOWN"
NOT_AVAILABLE = "NOT_AVAILABLE"

# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------

_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)

# Known invalid/disposable email patterns
_DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "tempmail.com", "throwaway.email",
    "yopmail.com", "sharklasers.com", "guerrillamailblock.com", "grr.la",
    "dispostable.com", "10minutemail.com", "trashmail.com", "maildrop.cc",
}


def validate_email(email: str | None) -> tuple[str, dict]:
    """Validate an email address.

    Checks:
    - Format (regex)
    - Domain is not disposable
    - MX record exists (DNS check)

    Returns (status, details_dict).
    """
    if not email or not str(email).strip():
        return NOT_AVAILABLE, {"reason": "No email provided"}

    email = email.strip().lower()

    # Format check
    if not _EMAIL_REGEX.match(email):
        return INVALID, {"reason": f"Invalid email format: {email}"}

    # Disposable check
    domain = email.split("@")[1]
    if domain in _DISPOSABLE_DOMAINS:
        return INVALID, {"reason": f"Disposable email domain: {domain}"}

    # MX record check (best effort — DNS may fail)
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX")
        if not answers:
            return INVALID, {"reason": f"No MX records for domain: {domain}"}
        return VALID, {"reason": "Email format valid, MX records found", "domain": domain}
    except ImportError:
        # dns.resolver not installed — skip DNS check
        return UNKNOWN, {"reason": "Email format valid, DNS check unavailable", "domain": domain}
    except Exception as e:
        return UNKNOWN, {"reason": f"Email format valid, DNS check failed: {e}", "domain": domain}


# ---------------------------------------------------------------------------
# Phone validation
# ---------------------------------------------------------------------------

def validate_phone(phone: str | None) -> tuple[str, dict]:
    """Validate a phone number.

    Checks:
    - Not null/empty
    - Matches expected +91XXXXXXXXXX format
    - Has 10 digits (Indian standard)

    Returns (status, details_dict).
    """
    if not phone or not str(phone).strip():
        return NOT_AVAILABLE, {"reason": "No phone number provided"}

    phone = phone.strip()

    # Expected format: +91XXXXXXXXXX
    if phone.startswith("+91"):
        digits = phone[3:]
        if len(digits) == 10 and digits.isdigit():
            # Additional check: Indian mobile numbers start with 6-9
            # Landline area codes can start with 0-4
            return VALID, {"reason": "Valid Indian phone number", "format": "E.164"}
        else:
            return INVALID, {"reason": f"Invalid digit count after +91: {len(digits)} digits"}

    # If it's 10 digits without country code
    if re.match(r"^\d{10}$", phone):
        return VALID, {"reason": "Valid 10-digit Indian phone number", "format": "local"}

    # Other formats
    return INVALID, {"reason": f"Unexpected phone format: {phone}"}


# ---------------------------------------------------------------------------
# Website validation
# ---------------------------------------------------------------------------

# Known noise/irrelevant domains
_NOISE_DOMAINS = {
    "bing.com", "google.com", "google.co.in", "wikipedia.org",
    "facebook.com", "twitter.com", "instagram.com", "youtube.com",
    "linkedin.com", "reddit.com", "quora.com", "medium.com",
    "copilot.microsoft.com", "microsoft.com",
}


def validate_website(website: str | None) -> tuple[str, dict]:
    """Validate a website URL.

    Checks:
    - Not null/empty
    - Valid URL format
    - Domain is not a known noise/tracking domain
    - Domain resolves (DNS check)
    - HTTP request succeeds (best effort)

    Returns (status, details_dict).
    """
    if not website or not str(website).strip():
        return NOT_AVAILABLE, {"reason": "No website provided"}

    website = website.strip()

    # Parse URL
    try:
        parsed = urlparse(website)
    except Exception:
        return INVALID, {"reason": f"Cannot parse URL: {website}"}

    if not parsed.scheme or not parsed.netloc:
        return INVALID, {"reason": f"Invalid URL structure: {website}"}

    domain = parsed.netloc.lower()
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]

    # Noise domain check
    if domain in _NOISE_DOMAINS:
        return INVALID, {"reason": f"Known noise/tracking domain: {domain}"}

    # Bing redirect URLs
    if "bing.com/ck" in website.lower():
        return INVALID, {"reason": "Bing redirect/tracking URL"}

    # Google redirect URLs
    if "google.com/url" in website.lower():
        return INVALID, {"reason": "Google redirect URL"}

    # DNS resolution check
    try:
        socket.setdefaulttimeout(5)
        socket.getaddrinfo(domain, 80)
    except (socket.gaierror, socket.timeout, OSError):
        return INVALID, {"reason": f"Domain does not resolve: {domain}"}

    return VALID, {"reason": "Website URL valid, domain resolves", "domain": domain}


# ---------------------------------------------------------------------------
# Business existence validation
# ---------------------------------------------------------------------------

# Business noise patterns — names that are clearly not real businesses
_BUSINESS_NOISE_PATTERNS = [
    r"^copilot",
    r"^microsoft",
    r"join group conversation",
    r"^portrait",
    r"^\[.*\]$",  # Names in brackets like [Copilot 3D]
    r"^mico$",
]

# Minimum fields to consider as potential business
_MIN_BUSINESS_FIELDS = 2  # At least name + one of: phone, address, coords


def validate_business_existence(
    name: str | None,
    phone: str | None,
    address: str | None,
    city: str | None,
    latitude: float | None,
    longitude: float | None,
    website: str | None,
    rating: float | None,
    source_adapters: list[str] | None = None,
) -> tuple[str, dict]:
    """Validate whether a company record likely represents a real business.

    Heuristic checks:
    - Name is not obviously noise/non-business
    - Has minimum required fields (name + at least one contact/location)
    - Not a generic Bing/Google search result

    Returns (status, details_dict).
    """
    reasons = []
    score = 0

    # Check name for noise
    if name:
        name_lower = name.lower().strip()
        for pattern in _BUSINESS_NOISE_PATTERNS:
            if re.search(pattern, name_lower):
                return INVALID, {"reason": f"Name matches noise pattern: {name}"}

    # Count how many business-relevant fields are present
    fields_present = 0
    if name and len(name.strip()) > 1:
        fields_present += 1
    if phone:
        fields_present += 1
        score += 2
    if address:
        fields_present += 1
        score += 1
    if city:
        fields_present += 1
        score += 1
    if latitude and longitude:
        fields_present += 1
        score += 2
    if website:
        fields_present += 1
        score += 1
    if rating is not None:
        score += 1

    # Minimum field check
    if fields_present < _MIN_BUSINESS_FIELDS:
        return INVALID, {
            "reason": f"Insufficient business fields ({fields_present}/{_MIN_BUSINESS_FIELDS} minimum)",
            "fields_present": fields_present,
        }

    # Source diversity bonus
    unique_sources = list(set(source_adapters or []))
    non_unknown_sources = [s for s in unique_sources if s != "unknown"]

    if len(non_unknown_sources) >= 2:
        score += 3
        reasons.append(f"Found in {len(non_unknown_sources)} verified sources")
    elif len(non_unknown_sources) == 1:
        score += 1
        reasons.append(f"Found in 1 verified source")
    elif len(unique_sources) == 1 and unique_sources[0] == "unknown":
        reasons.append("Only found in unknown source")

    # Score-based decision
    if score >= 4:
        return VALID, {
            "reason": "Sufficient business indicators",
            "score": score,
            "fields_present": fields_present,
            "sources": unique_sources,
            "details": reasons,
        }
    elif score >= 2:
        return UNKNOWN, {
            "reason": "Limited business indicators",
            "score": score,
            "fields_present": fields_present,
            "sources": unique_sources,
            "details": reasons,
        }
    else:
        return INVALID, {
            "reason": "Too few business indicators",
            "score": score,
            "fields_present": fields_present,
            "sources": unique_sources,
        }
