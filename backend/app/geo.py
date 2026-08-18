"""
url: /backend/app/geo.py
About:
  Single source of truth for all geographic and category configuration.
  Replaces hardcoded city_coords, city_districts, INDIAN_STATES, and
  CATEGORY_SYNONYMS scattered across adapter files. All adapters import
  from this module instead of maintaining their own copies.
"""

from typing import Any

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
    "guntur": (16.3067, 80.4365),
    "tirupati": (13.6288, 79.4192),
    "warangal": (17.9784, 79.5941),
    "nellore": (14.4426, 79.9865),
    "kurnool": (15.8281, 78.0373),
    "rajamahendravaram": (17.0005, 81.8040),
    "kakinada": (16.9891, 82.2475),
    "bhimavaram": (16.5449, 81.5212),
    "narsapur": (16.4360, 81.6690),
    "tadepalligudem": (16.8147, 81.5272),
}

CITY_DISTRICTS: dict[str, str] = {
    "eluru": "West Godavari district",
    "hyderabad": "Hyderabad district",
    "bangalore": "Bangalore Urban district",
    "bengaluru": "Bangalore Urban district",
    "chennai": "Chennai district",
    "mumbai": "Mumbai district",
    "delhi": "New Delhi",
    "pune": "Pune district",
    "vijayawada": "Krishna district",
    "visakhapatnam": "Visakhapatnam district",
    "guntur": "Guntur district",
    "tirupati": "Chittoor district",
    "warangal": "Warangal district",
    "nellore": "Nellore district",
    "kurnool": "Kurnool district",
    "rajamahendravaram": "East Godavari district",
    "kakinada": "East Godavari district",
    "bhimavaram": "West Godavari district",
    "narsapur": "West Godavari district",
    "tadepalligudem": "West Godavari district",
    "jaggayyapeta": "Krishna district",
    "mangalagiri": "Guntur district",
    "tiruvananthapuram": "Thiruvananthapuram district",
    "kozhikode": "Kozhikode district",
    "thrissur": "Thrissur district",
    "coimbatore": "Coimbatore district",
    "madurai": "Madurai district",
    "jaipur": "Jaipur district",
    "lucknow": "Lucknow district",
    "kanpur": "Kanpur district",
    "nagpur": "Nagpur district",
    "ahmedabad": "Ahmedabad district",
    "surat": "Surat district",
    "indore": "Indore district",
    "bhopal": "Bhopal district",
    "patna": "Patna district",
    "kolkata": "Kolkata district",
    "agra": "Agra district",
    "varanasi": "Varanasi district",
}

CATEGORY_SYNONYMS: dict[str, list[str]] = {
    "hospitals": ["hospitals", "medical centers"],
    "hospital": ["hospital", "medical center", "hospitals"],
    "restaurants": ["restaurants", "food courts"],
    "schools": ["schools", "colleges"],
    "shops": ["shops", "stores"],
    "hotels": ["hotels", "lodges"],
    "pharmacies": ["pharmacies", "medical stores"],
    "clinics": ["clinics", "polyclinics"],
    "startups": ["startups", "tech companies"],
    "it companies": ["IT companies", "software companies", "technology firms"],
    "manufacturers": ["manufacturers", "factories", "industrial units"],
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

LOCATION_MATCH_RADIUS_DEGREES: float = 0.25
ENTITY_MATCH_RADIUS_DEGREES: float = 0.0005


def get_coords_for_city(city: str) -> tuple[float, float] | None:
    """Look up coordinates for a city name. Returns (lat, lng) or None."""
    return CITY_COORDS.get(city.lower().strip())


def get_district_for_city(city: str) -> str | None:
    """Look up district for a city name. Returns district string or None."""
    return CITY_DISTRICTS.get(city.lower().strip())


def is_state_name(text: str) -> bool:
    """Check if text matches a known Indian state name."""
    return text.lower().strip() in INDIAN_STATES_LOWER


def get_category_synonyms(category: str) -> list[str]:
    """Get query variations for a category. Falls back to [category] if no match."""
    cat_lower = category.lower().strip()
    for key, synonyms in CATEGORY_SYNONYMS.items():
        if key in cat_lower or cat_lower in key:
            return synonyms
    return [category]


def build_location_scopes(location: str) -> list[str]:
    """Generate broader geographic scopes from a location string.
    'Eluru, Andhra Pradesh' -> ['Eluru', 'Eluru Andhra Pradesh', 'West Godavari district']
    """
    parts = [p.strip() for p in location.split(",")]
    city = parts[0] if parts else location
    state = parts[1].strip() if len(parts) > 1 else ""

    scopes: list[str] = [city]
    if state:
        scopes.append(f"{city} {state}")

    city_lower = city.lower()
    district = CITY_DISTRICTS.get(city_lower)
    if district:
        if district not in scopes:
            scopes.append(district)
    else:
        guessed = f"{city} district"
        if guessed not in scopes:
            scopes.append(guessed)

    if state and len(scopes) < 3:
        scopes.append(f"{city} {state} India")

    return scopes[:3]
