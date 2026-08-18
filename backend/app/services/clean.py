"""
url: /backend/app/services/clean.py
About:
  Level 3 cleaning and standardization operations. Reads raw_data fields
  and produces normalized versions. No external API calls — pure string
  processing. Each operation is stateless and testable independently.
"""

import re
import unicodedata
from typing import Any

from app.geo import INDIAN_STATES, INDIAN_STATES_LOWER


# ---------------------------------------------------------------------------
# Name standardization
# ---------------------------------------------------------------------------

_SUFFIXES_TO_REMOVE = [
    "pvt ltd", "pvt. ltd.", "private limited", "ltd", "limited",
    "llp", "llc", "inc", "incorp", "corp", "corporation",
    "co", "company", "enterprises", "enterprise",
    "and sons", "& sons",
]

_LOCATIONAL_SUFFIXES = [
    r",\s*eluru$",
    r",\s*bangalore$",
    r",\s*bengaluru$",
    r",\s*hyderabad$",
    r",\s*chennai$",
    r",\s*mumbai$",
    r",\s*delhi$",
    r",\s*vijayawada$",
    r",\s*visakhapatnam$",
    r",\s*guntur$",
    r",\s*tirupati$",
    r",\s*warangal$",
    r",\s*nellore$",
    r",\s*kurnool$",
    r",\s*rajamahendravaram$",
    r",\s*kakinada$",
    r",\s*bhimavaram$",
    r",\s*narsapur$",
    r",\s*tadepalligudem$",
]


def standardize_name(name: str | None) -> str | None:
    """Standardize a business/company name.

    - Strip leading/trailing whitespace
    - Normalize unicode
    - Collapse multiple spaces
    - Split on pipe/dash separators and take the primary name
    - Remove trailing city names (e.g., "Aayush Hospitals, Eluru" -> "Aayush Hospitals")
    - Title-case the result
    """
    if not name:
        return None

    name = name.strip()
    if not name:
        return None

    # Normalize unicode
    name = unicodedata.normalize("NFKC", name)

    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name).strip()

    # Split on pipe | dash - colon : and take the first (primary) name
    # e.g., "Life Hospitals | Orthopedic Hospital in Eluru" -> "Life Hospitals"
    # e.g., "District Hospital - Eluru" -> "District Hospital"
    name = re.split(r"\s*[\|\-]\s*", name)[0].strip()

    # Remove trailing city names
    for pattern in _LOCATIONAL_SUFFIXES:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE).strip()

    # Title case
    name = name.title()

    return name if name else None


def name_for_matching(name: str | None) -> str:
    """Produce a normalized name for entity resolution comparison.

    More aggressive than standardize_name — strips all non-alphanumeric
    characters and lowercases for fuzzy matching. Also removes descriptions
    after pipe/dash/colon separators.
    """
    if not name:
        return ""
    name = name.lower()
    # Split on separators and take primary name
    name = re.split(r"\s*[\|\-:]\s*", name)[0].strip()
    # Remove all non-alphanumeric except spaces
    name = re.sub(r"[^a-z0-9\s]", "", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    # Remove common suffixes
    for suffix in _SUFFIXES_TO_REMOVE:
        name = name.replace(suffix, "")
    return name.strip()


# ---------------------------------------------------------------------------
# Phone normalization
# ---------------------------------------------------------------------------

def normalize_phone(phone: str | None) -> str | None:
    """Normalize an Indian phone number to a consistent format.

    Input formats handled:
    - 095151 15103
    - 088122 27755
    - +91 95151 15103
    - 919515115103
    - 080 49653185
    - 9876543210

    Output: "+91XXXXXXXXXX" (E.164-like) or None
    """
    if not phone:
        return None

    # Strip all non-digit characters
    digits = re.sub(r"\D", "", phone)

    if not digits:
        return None

    # Remove leading zeros
    digits = digits.lstrip("0")

    # If starts with 91 and has 12 digits, it's already country code
    if len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"

    # If 10 digits, assume Indian mobile
    if len(digits) == 10:
        return f"+91{digits}"

    # If 11 digits starting with 0, drop the 0
    if len(digits) == 11 and digits.startswith("0"):
        return f"+91{digits[1:]}"

    # If starts with +91 already handled above
    if phone.startswith("+"):
        return f"+{digits}" if len(digits) >= 10 else None

    # Landline with area code (080 XXXXXXX)
    if len(digits) >= 10:
        return f"+91{digits[-10:]}"

    return None


def phone_display(phone: str | None) -> str | None:
    """Format phone for display: 0XXXXXXXXX or +91 XXXXXXXXXX."""
    normalized = normalize_phone(phone)
    if not normalized:
        return None
    # Extract 10-digit local number
    local = normalized[-10:]
    return f"0{local}"


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

def normalize_url(url: str | None) -> str | None:
    """Normalize a website URL.

    - Add https:// if missing
    - Remove trailing slashes
    - Remove tracking parameters
    - Lowercase scheme and domain
    """
    if not url:
        return None

    url = url.strip()
    if not url:
        return None

    # Skip Bing redirect URLs (they're tracking URLs, not business websites)
    if "bing.com/ck" in url.lower():
        return None

    # Skip Google redirect URLs
    if "google.com/url" in url.lower():
        return None

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    # Lowercase scheme
    url = re.sub(r"^http://", "https://", url, flags=re.IGNORECASE)

    # Remove trailing slash
    url = url.rstrip("/")

    # Remove common tracking params
    url = re.sub(r"[?&](utm_\w+=[^&]*)", "", url)
    url = re.sub(r"[?&](ref=[^&]*)", "", url)
    url = re.sub(r"\?$", "", url)

    return url


# ---------------------------------------------------------------------------
# Address standardization
# ---------------------------------------------------------------------------

_STATE_ABBREVIATIONS = {
    "AP": "Andhra Pradesh",
    "AR": "Arunachal Pradesh",
    "AS": "Assam",
    "BR": "Bihar",
    "CG": "Chhattisgarh",
    "GA": "Goa",
    "GJ": "Gujarat",
    "HR": "Haryana",
    "HP": "Himachal Pradesh",
    "JH": "Jharkhand",
    "KA": "Karnataka",
    "KL": "Kerala",
    "MP": "Madhya Pradesh",
    "MH": "Maharashtra",
    "MN": "Manipur",
    "ML": "Meghalaya",
    "MZ": "Mizoram",
    "NL": "Nagaland",
    "OD": "Odisha",
    "OR": "Odisha",
    "PB": "Punjab",
    "RJ": "Rajasthan",
    "SK": "Sikkim",
    "TN": "Tamil Nadu",
    "TS": "Telangana",
    "TR": "Tripura",
    "UP": "Uttar Pradesh",
    "UK": "Uttarakhand",
    "WB": "West Bengal",
    "DL": "Delhi",
}


def standardize_state(state: str | None) -> str | None:
    """Standardize an Indian state name.

    - Expand abbreviations (AP -> Andhra Pradesh)
    - Title case
    - Match against known states
    """
    if not state:
        return None

    state = state.strip()
    if not state:
        return None

    # Check abbreviation
    upper = state.upper()
    if upper in _STATE_ABBREVIATIONS:
        return _STATE_ABBREVIATIONS[upper]

    # Check exact match (case-insensitive)
    for known_state in INDIAN_STATES:
        if known_state.lower() == state.lower():
            return known_state

    # Title case as fallback
    return state.title()


def standardize_address(address: str | None) -> str | None:
    """Standardize an address string.

    - Normalize whitespace
    - Normalize common abbreviations
    - Ensure proper comma separation
    """
    if not address:
        return None

    address = address.strip()
    if not address:
        return None

    # Normalize unicode
    address = unicodedata.normalize("NFKC", address)

    # Common abbreviation expansions
    _abbrevs = {
        r"\bSt\b": "Street",
        r"\bRd\b": "Road",
        r"\bAve\b": "Avenue",
        r"\bBlvd\b": "Boulevard",
        r"\bDr\b": "Drive",
        r"\bLn\b": "Lane",
        r"\bCt\b": "Court",
        r"\bPl\b": "Place",
        r"\bHr\b": "Harbour",
        r"\bNagar\b": "Nagar",
        r"\bColony\b": "Colony",
    }
    for pattern, replacement in _abbrevs.items():
        address = re.sub(pattern, replacement, address)

    # Collapse multiple spaces
    address = re.sub(r"\s+", " ", address).strip()

    return address


# ---------------------------------------------------------------------------
# City normalization
# ---------------------------------------------------------------------------

# Common city name variants
_CITY_ALIASES = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "trivandrum": "Thiruvananthapuram",
    "cochin": "Kochi",
    "poona": "Pune",
}


def standardize_city(city: str | None) -> str | None:
    """Standardize a city name."""
    if not city:
        return None

    city = city.strip()
    if not city:
        return None

    lower = city.lower()
    if lower in _CITY_ALIASES:
        return _CITY_ALIASES[lower]

    return city.title()


# ---------------------------------------------------------------------------
# Completeness scoring
# ---------------------------------------------------------------------------

def compute_completeness(raw_data: dict[str, Any]) -> float:
    """Compute a completeness score (0.0-1.0) for a raw record.

    Weights: name (0.25), phone (0.20), address (0.15), website (0.15),
    city (0.10), lat/lng (0.10), rating (0.05)
    """
    weights = {
        "name": 0.25,
        "phone": 0.20,
        "address": 0.15,
        "website": 0.15,
        "city": 0.10,
        "lat_lng": 0.10,
        "rating": 0.05,
    }

    score = 0.0
    if raw_data.get("name"):
        score += weights["name"]
    if raw_data.get("phone"):
        score += weights["phone"]
    if raw_data.get("address"):
        score += weights["address"]
    if raw_data.get("website"):
        score += weights["website"]
    if raw_data.get("city"):
        score += weights["city"]
    if raw_data.get("latitude") and raw_data.get("longitude"):
        score += weights["lat_lng"]
    if raw_data.get("rating") is not None:
        score += weights["rating"]

    return round(score, 2)


# ---------------------------------------------------------------------------
# Master clean function
# ---------------------------------------------------------------------------

def clean_raw_data(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Apply all Level 3 cleaning operations to a raw_data dict.

    Returns a new dict with cleaned fields. Original raw_data is not modified.
    Also returns a dict of changes made for audit trail.
    """
    cleaned = dict(raw_data)
    changes: list[str] = []

    # 1. Standardize name
    original_name = raw_data.get("name")
    cleaned_name = standardize_name(original_name)
    if cleaned_name != original_name:
        changes.append(f"name: '{original_name}' -> '{cleaned_name}'")
    cleaned["name"] = cleaned_name

    # 2. Normalize phone
    original_phone = raw_data.get("phone")
    cleaned_phone = normalize_phone(original_phone)
    if cleaned_phone != original_phone:
        changes.append(f"phone: '{original_phone}' -> '{cleaned_phone}'")
    cleaned["phone"] = cleaned_phone
    cleaned["phone_display"] = phone_display(cleaned_phone)

    # 3. Normalize website
    original_website = raw_data.get("website")
    cleaned_website = normalize_url(original_website)
    if cleaned_website != original_website:
        changes.append(f"website: '{original_website}' -> '{cleaned_website}'")
    cleaned["website"] = cleaned_website

    # 4. Standardize address
    original_address = raw_data.get("address")
    cleaned_address = standardize_address(original_address)
    if cleaned_address != original_address:
        changes.append(f"address: '{original_address}' -> '{cleaned_address}'")
    cleaned["address"] = cleaned_address

    # 5. Standardize city
    original_city = raw_data.get("city")
    cleaned_city = standardize_city(original_city)
    if cleaned_city != original_city:
        changes.append(f"city: '{original_city}' -> '{cleaned_city}'")
    cleaned["city"] = cleaned_city

    # 6. Standardize state
    original_state = raw_data.get("state")
    cleaned_state = standardize_state(original_state)
    if cleaned_state != original_state:
        changes.append(f"state: '{original_state}' -> '{cleaned_state}'")
    cleaned["state"] = cleaned_state

    # 7. Compute completeness
    cleaned["completeness_score"] = compute_completeness(cleaned)

    # Store cleaning metadata
    cleaned["_level3_cleaned"] = True
    cleaned["_level3_changes"] = changes

    return cleaned
