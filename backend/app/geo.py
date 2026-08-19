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

# Broad category keyword groups for relevance validation.
# A result is relevant if ANY keyword from the group appears in its data.
# This is NOT an allowlist — it's a relevance heuristic.
CATEGORY_KEYWORD_GROUPS: dict[str, list[str]] = {
    "hospital": ["hospital", "medical", "healthcare", "clinic", "diagnostic", "nursing", "care", "surgery", "health"],
    "restaurant": ["restaurant", "cafe", "café", "dining", "food", "bistro", "grill", "pizza", "kitchen", "eatery", "bar", "pub"],
    "hotel": ["hotel", "motel", "inn", "resort", "lodge", "accommodation", "hostel", "lodging"],
    "school": ["school", "academy", "education", "learning", "tuition"],
    "college": ["college", "university", "institute", "education", "campus"],
    "shop": ["shop", "store", "retail", "mart", "market", "mall", "outlet", "boutique"],
    "clothing": ["clothing", "clothes", "fashion", "apparel", "garment", "wear", "textile", "boutique"],
    "pharmacy": ["pharmacy", "pharmaceutical", "drugstore", "chemist", "medicine", "drug"],
    "dentist": ["dental", "dentist", "orthodont", "tooth", "oral"],
    "clinic": ["clinic", "medical", "healthcare", "doctor", "physician", "diagnostic"],
    "bank": ["bank", "financial", "finance", "credit", "loan", "insurance"],
    "gym": ["gym", "fitness", "health club", "yoga", "workout", "exercise"],
    "salon": ["salon", "beauty", "spa", "parlor", "parlor", "hair", "nail"],
    "auto": ["auto", "car", "vehicle", "automobile", "motor", "garage", "workshop"],
    "real estate": ["real estate", "property", "realtor", "realty", "construction", "builder"],
    "lawyer": ["lawyer", "attorney", "legal", "advocate", "law firm", "counsel"],
    "accounting": ["accountant", "accounting", "CA", "chartered accountant", "tax"],
    "it": ["software", "IT", "technology", "tech", "digital", "computer", "data", "cloud", "SaaS", "startup"],
    "manufacturing": ["manufacturing", "factory", "industrial", "production", "plant", "fabricat"],
    "consulting": ["consulting", "consultant", "advisory", "management", "strategy"],
    "logistics": ["logistics", "shipping", "freight", "cargo", "delivery", "transport", "courier"],
    "restaurant_india": ["restaurant", "food", "dining", "cafe", "biryani", "tiffin", "mess", "canteen"],
}


def get_coords_for_city(city: str) -> tuple[float, float] | None:
    """Look up coordinates for a city name. Returns (lat, lng) or None."""
    return CITY_COORDS.get(city.lower().strip())


def is_state_name(text: str) -> bool:
    """Check if text matches a known Indian state name."""
    return text.lower().strip() in INDIAN_STATES_LOWER


def get_category_synonyms(category: str) -> list[str]:
    """Get related keywords for a category from CATEGORY_KEYWORD_GROUPS.
    
    Used by search adapters to generate query variations.
    Returns a list of related keywords (not an allowlist).
    """
    cat_lower = category.lower().strip()
    for key, keywords in CATEGORY_KEYWORD_GROUPS.items():
        if key in cat_lower or cat_lower in key:
            return keywords
    # Fallback: return the original category
    return [category]


def _extract_category_keywords(category: str) -> set[str]:
    """Extract meaningful keywords from a category string.
    
    'clothing shops in Hyderabad' -> {'clothing', 'shops'}
    'restaurants' -> {'restaurants'}
    'software companies' -> {'software', 'companies'}
    'startups' -> {'startups'}
    """
    stop_words = {
        "in", "near", "at", "around", "from", "the", "a", "an",
        "and", "or", "of", "for", "with", "to", "top", "best",
        "companies", "company", "firms", "firm", "businesses", "business",
        "services", "service", "providers", "provider",
        "shops", "shop", "stores", "store",
        "centers", "centre", "center", "centers",
        "near", "around", "within",
    }
    words = re.findall(r"[a-zA-Z]+", category.lower())
    return {w for w in words if w not in stop_words and len(w) > 2}


def check_category_relevance(record: dict, category: str) -> bool:
    """Check if a record is relevant to the requested category.
    
    Uses keyword-based matching against the record's name, industry,
    address, source_url, and metadata. This is a HEURISTIC, not an
    allowlist — it checks semantic relevance, not category membership.
    
    Returns True if the record is plausibly relevant.
    Returns True if relevance cannot be determined (fail-open).
    """
    if not category:
        return True

    raw = record.get("raw_data", {})
    # Build text but exclude metadata dict repr
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

    cat_keywords = _extract_category_keywords(category)
    if not cat_keywords:
        return True

    # 1. Direct keyword match
    for kw in cat_keywords:
        if kw in text:
            return True

    # 2. Expand category keywords using CATEGORY_KEYWORD_GROUPS
    # "dentists" -> look up "dentist" group -> ["dental", "dentist", "orthodont", ...]
    # "startups" -> look up "it" group (has "startup") -> ["software", "technology", ...]
    all_group_keywords = set()
    for key, keywords in CATEGORY_KEYWORD_GROUPS.items():
        # Match if key (or key+s) is in category using word boundaries
        # Skip short/generic keys like "shop" to avoid false matches
        if len(key) >= 5:
            key_pattern = r'\b' + re.escape(key) + r'(s|es)?\b'
            if re.search(key_pattern, category.lower()):
                all_group_keywords.update(kw.lower() for kw in keywords)
        # Also match if any group keyword is a stem-variant of the category
        for kw in keywords:
            kw_lower = kw.lower()
            if len(kw_lower) >= 6 and kw_lower in category.lower():
                all_group_keywords.update(k.lower() for k in keywords)
                break
    # Also check each extracted keyword against groups
    for kw in cat_keywords:
        for key, keywords in CATEGORY_KEYWORD_GROUPS.items():
            if kw in key or key in kw:
                all_group_keywords.update(k.lower() for k in keywords)
    # Check group keywords against record text
    for gkw in all_group_keywords:
        if gkw in text:
            return True
    # Also check each extracted keyword against groups
    for kw in cat_keywords:
        for key, keywords in CATEGORY_KEYWORD_GROUPS.items():
            if kw in key or key in kw:
                all_group_keywords.update(k.lower() for k in keywords)
    # Check group keywords against record text
    for gkw in all_group_keywords:
        if gkw in text:
            return True

    # 3. Word-level stem match: "dentists" vs "dental" share "dent" prefix
    text_words = set(re.findall(r"[a-zA-Z]{4,}", text))
    cat_words = set(re.findall(r"[a-zA-Z]{4,}", category.lower()))
    all_words = cat_words | all_group_keywords
    for aw in all_words:
        for tw in text_words:
            if len(aw) >= 5 and len(tw) >= 5:
                # Check 5-char prefix match
                if aw[:5] == tw[:5]:
                    return True

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
