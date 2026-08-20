"""
url: /backend/app/geo.py
About:
  Single source of truth for all geographic and category configuration.
  Contains city coordinates for fast lookup, category relevance validation,
  and utility functions. OSM tags/CATEGORY_SYNONYMS are NOT gatekeepers —
  the user's natural-language query is the source of truth.
"""

from typing import Any
import re

INDIAN_STATES: list[str] = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi",
]

INDIAN_STATES_LOWER: set[str] = {s.lower() for s in INDIAN_STATES}

CITY_COORDS: dict[str, tuple[float, float]] = {
    "eluru": (16.7104, 81.1154),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "mumbai": (19.0760, 72.8777),
    "pune": (18.5204, 73.8567),
    "delhi": (28.6139, 77.2090),
    "vijayawada": (16.5062, 80.6480),
    "visakhapatnam": (17.6868, 83.2185),
    "vizag": (17.6868, 83.2185),
    "guntur": (16.3067, 80.4365),
    "tirupati": (13.6288, 79.4192),
    "warangal": (17.9784, 79.5941),
    "nellore": (14.4426, 79.9865),
    "kurnool": (15.8281, 78.0373),
    "rajamahendravaram": (17.0005, 81.8040),
    "rajahmundry": (17.0005, 81.8040),
    "kakinada": (16.9891, 82.2475),
    "bhimavaram": (16.5449, 81.5212),
    "narsapur": (16.4360, 81.6690),
    "tadepalligudem": (16.8147, 81.5272),
    "london": (51.5074, -0.1278),
    "toronto": (43.6532, -79.3832),
    "new york": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298),
    "san francisco": (37.7749, -122.4194),
    "seattle": (47.6062, -122.3321),
    "boston": (42.3601, -71.0589),
    "miami": (25.7617, -80.1918),
    "dallas": (32.7767, -96.7970),
    "houston": (29.7604, -95.3698),
    "paris": (48.8566, 2.3522),
    "berlin": (52.5200, 13.4050),
    "tokyo": (35.6762, 139.6503),
    "sydney": (-33.8688, 151.2093),
    "melbourne": (-37.8136, 144.9631),
    "singapore": (1.3521, 103.8198),
    "dubai": (25.2048, 55.2708),
    "mexico city": (19.4326, -99.1332),
    "mexico": (19.4326, -99.1332),
    "sao paulo": (-23.5505, -46.6333),
    "cairo": (30.0444, 31.2357),
    "lagos": (6.5244, 3.3792),
    "nairobi": (-1.2921, 36.8219),
    "cape town": (-33.9249, 18.4241),
    "bangkok": (13.7563, 100.5018),
    "hong kong": (22.3193, 114.1694),
    "shanghai": (31.2304, 121.4737),
    "beijing": (39.9042, 116.4074),
    "mumbai": (19.0760, 72.8777),
    "kolkata": (22.5726, 88.3639),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "kochi": (9.9312, 76.2673),
    "bhopal": (23.2599, 77.4126),
    "nagpur": (21.1458, 79.0882),
    "patna": (25.6093, 85.1376),
    "indore": (22.7196, 75.8577),
    "coimbatore": (11.0168, 76.9558),
    "madurai": (9.9252, 78.1198),
    "thiruvananthapuram": (8.5241, 76.9366),
    "varanasi": (25.3176, 82.9739),
    "agra": (27.1767, 78.0081),
    "kanpur": (26.4499, 80.3319),
    "nashik": (19.9975, 73.7898),
}

GENERIC_BUSINESS_SUFFIXES: list[str] = [
    "hospital", "medical", "center", "centre", "clinic", "labs",
    "diagnostic", "healthcare", "nursing", "care", "pharmacy",
    "solutions", "consulting", "technologies", "services", "enterprises",
    "industries", "traders", "suppliers", "dealers", "distributors",
    "restaurants", "hotels", "resorts", "stores", "shops", "malls",
    "academy", "institute", "school", "college", "university",
]

GENERIC_SKIP_WORDS: list[str] = [
    "wikipedia", "youtube", "facebook", "twitter",
    "quora", "reddit", "linkedin", "instagram", "news",
    "article", "blog", "list of", "best", "top",
    "who.int", "government", "ministry", "directory",
]

GENERIC_NAME_PATTERN: str = (
    r"([A-Z][A-Za-z\s&'.\-]{2,80})\s*[-–:,]\s*(.{10,200})"
)

LOCATION_MATCH_RADIUS_DEGREES: float = 0.45
ENTITY_MATCH_RADIUS_DEGREES: float = 0.0005


def get_coords_for_city(city: str) -> tuple[float, float] | None:
    """Look up coordinates for a city name. Returns (lat, lng) or None."""
    return CITY_COORDS.get(city.lower().strip())


def is_state_name(text: str) -> bool:
    """Check if text matches a known Indian state name."""
    return text.lower().strip() in INDIAN_STATES_LOWER


def get_category_synonyms(category: str) -> list[str]:
    """Get search query variations for a category.
    
    Returns the raw category and common variations. Does NOT use any
    predefined keyword groups — the user's query determines the search.
    """
    cat_lower = category.lower().strip()
    variations = [category]
    
    # Add singular/plural variations (threshold >3 so "spas" -> "spa")
    if cat_lower.endswith("s") and len(cat_lower) > 3:
        variations.append(cat_lower[:-1])
    elif not cat_lower.endswith("s"):
        variations.append(cat_lower + "s")
    
    return list(dict.fromkeys(variations))


def check_category_relevance(record: dict, category: str) -> bool:
    """Check if a record is plausibly relevant to the requested category.
    
    This is a PERMISSIVE filter — it only rejects records that are clearly
    unrelated. It does NOT use any predefined keyword allowlist. The user's
    query determines what is relevant, not a hardcoded category map.
    
    Strategy:
    - Fail-open: if we can't determine relevance, accept the record
    - Accept if ANY word from the category appears as a WHOLE WORD in the record text
    - Accept empty/unstructured records (let other filters handle quality)
    - Only reject if record has text but ZERO whole-word overlap with category
    """
    if not category:
        return True

    raw = record.get("raw_data", {})
    # Build text from record fields, exclude metadata dict repr
    meta = raw.get("metadata")
    meta_str = "" if meta is None or meta == {} else str(meta)
    text = " ".join([
        raw.get("name") or "",
        raw.get("industry") or "",
        raw.get("address") or "",
        raw.get("city") or "",
        raw.get("source_url") or "",
        raw.get("maps_url") or "",
        meta_str,
    ]).lower()

    # Fail-open: no text data means we can't judge relevance
    if not text.strip():
        return True

    # Extract meaningful words from the category (skip tiny/generic words)
    cat_words = set(re.findall(r"[a-zA-Z]{3,}", category.lower()))
    # Skip generic prepositions/articles AND generic business suffixes
    # These words appear in many business names but don't indicate category
    generic_words = {
        "the", "and", "for", "with", "near", "around", "from", "that", "this",
        "shop", "shops", "store", "stores", "center", "centre", "company",
        "companies", "business", "services", "service", "solutions",
        "enterprises", "industries", "traders", "dealers", "distributors",
        "suppliers", "agency", "agencies", "group", "associates", "partners",
    }
    cat_words -= generic_words
    if not cat_words:
        return True

    # Extract whole words from record text for boundary-aware matching
    text_words = set(re.findall(r"[a-zA-Z]{3,}", text))

    # Accept if ANY category word appears as a WHOLE WORD in record text
    for cw in cat_words:
        # Exact whole-word match
        if re.search(rf"\b{re.escape(cw)}\b", text):
            return True
        if cw in text_words:
            return True

        # Singular/plural stem match: "spas" matches "spa", "restaurants" matches "restaurant"
        # Strip trailing "s" from either side and check whole-word match
        stem = cw.rstrip("s") if cw.endswith("s") and len(cw) > 3 else cw
        if stem != cw:
            # Category word is plural (e.g., "spas"), check singular in text
            if re.search(rf"\b{re.escape(stem)}\b", text):
                return True
            if stem in text_words:
                return True
        # Also try adding "s" if category word is singular (e.g., "spa" -> check "spas" in text)
        if not cw.endswith("s"):
            plural = cw + "s"
            if re.search(rf"\b{re.escape(plural)}\b", text):
                return True
            if plural in text_words:
                return True

    # No whole-word overlap found.
    # Accept records with real business contact data (phone or address)
    # even without category word overlap — adapters already filter by relevance.
    phone = (raw.get("phone") or "").strip()
    address = (raw.get("address") or "").strip()
    if phone or address:
        return True

    # No overlap AND no contact data — check if record has analyzable content
    name = (raw.get("name") or "").strip()
    industry = (raw.get("industry") or "").strip()
    has_analyzable_content = bool(name or industry)

    if not has_analyzable_content:
        return True

    # Record has text but NO word overlap AND no contact data — reject
    return False


def build_location_scopes(location: str) -> list[str]:
    """Generate geographic scopes from a location string.
    
    Always includes the raw user-provided location as the primary scope.
    Does NOT substitute nearby or different cities.
    """
    if not location or not location.strip():
        return [""]

    raw = location.strip()
    parts = [p.strip() for p in raw.split(",")]
    city = parts[0]
    state = parts[1].strip() if len(parts) > 1 else ""

    scopes: list[str] = [raw]

    if city != raw:
        scopes.append(city)

    if state:
        combo = f"{city} {state}"
        if combo not in scopes:
            scopes.append(combo)

    return scopes[:3]
