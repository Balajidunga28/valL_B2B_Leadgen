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
    "rajahmundry": (17.0005, 81.8040),
    "vishakhapatnam": (17.6868, 83.2185),
    "tirupati": (13.6288, 79.4192),
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
    "hospitals": ["hospitals", "medical centers", "healthcare"],
    "hospital": ["hospital", "medical center", "hospitals", "healthcare"],
    "restaurants": ["restaurants", "food", "dining"],
    "restaurant": ["restaurant", "restaurants", "food", "dining"],
    "schools": ["schools", "education"],
    "school": ["school", "schools", "education"],
    "shops": ["shops", "stores", "retail"],
    "shop": ["shop", "shops", "stores", "retail"],
    "hotels": ["hotels", "accommodation", "lodging"],
    "hotel": ["hotel", "hotels", "accommodation", "lodging"],
    "pharmacies": ["pharmacies", "pharmacy", "drugstore"],
    "pharmacy": ["pharmacy", "pharmacies", "drugstore"],
    "clinics": ["clinics", "clinic", "medical"],
    "clinic": ["clinic", "clinics", "medical"],
    "startups": ["startups", "startup", "tech companies"],
    "startup": ["startup", "startups", "tech companies"],
    "it companies": ["IT companies", "software companies", "technology firms"],
    "software companies": ["software companies", "IT companies", "technology firms", "software"],
    "manufacturers": ["manufacturers", "factories", "industrial"],
    "manufacturer": ["manufacturer", "manufacturers", "factories"],
    "dentists": ["dentists", "dental", "dental clinic", "dental care"],
    "dentist": ["dentist", "dentists", "dental", "dental clinic"],
    "dental": ["dental", "dentist", "dentists", "dental clinic"],
    "gym": ["gym", "fitness", "fitness centre", "fitness center", "health club"],
    "gyms": ["gyms", "fitness", "fitness centres", "fitness centers"],
    "fitness": ["fitness", "gym", "fitness centre", "fitness center"],
    "banks": ["banks", "bank", "financial"],
    "bank": ["bank", "banks", "financial"],
    "atm": ["ATM", "atm", "cash machine"],
    "salons": ["salons", "salon", "beauty parlor", "beauty salon"],
    "salon": ["salon", "salons", "beauty parlor", "beauty salon"],
    "beauty": ["beauty", "beauty salon", "beauty parlor", "spa"],
    "spa": ["spa", "spas", "wellness", "beauty"],
    "supermarkets": ["supermarkets", "supermarket", "grocery", "grocery store"],
    "supermarket": ["supermarket", "supermarkets", "grocery", "grocery store"],
    "grocery": ["grocery", "grocery store", "supermarket"],
    "car": ["car", "automobile", "vehicle", "auto"],
    "automobile": ["automobile", "car", "vehicle", "auto"],
    "clothing": ["clothing", "clothes", "fashion", "apparel"],
    "fashion": ["fashion", "clothing", "clothes", "apparel"],
    "electronics": ["electronics", "electronic", "gadget"],
    "pet": ["pet", "pets", "pet shop", "pet store", "animal"],
    "lawyer": ["lawyer", "lawyers", "attorney", "legal", "advocate"],
    "legal": ["legal", "lawyer", "lawyers", "attorney", "advocate"],
    "accounting": ["accounting", "accountant", "CA", "chartered accountant"],
    "real estate": ["real estate", "property", "realty"],
    "schools": ["schools", "education", "learning"],
    "colleges": ["colleges", "college", "education", "university"],
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


def get_district_for_city(city: str) -> str | None:
    """Look up district for a city name. Returns district string or None."""
    return CITY_DISTRICTS.get(city.lower().strip())


def is_state_name(text: str) -> bool:
    """Check if text matches a known Indian state name."""
    return text.lower().strip() in INDIAN_STATES_LOWER


def get_category_synonyms(category: str) -> list[str]:
    """Get query variations for a category. Falls back to [category] if no match.
    
    For multi-word queries like 'software companies', generates useful
    variations. For single words like 'dentists', looks up synonyms.
    Always returns the original category first.
    """
    cat_lower = category.lower().strip()
    if not cat_lower:
        return [category]

    # Exact match in synonym map
    if cat_lower in CATEGORY_SYNONYMS:
        return CATEGORY_SYNONYMS[cat_lower]

    # Partial match - check if any key is contained in the query
    for key, synonyms in CATEGORY_SYNONYMS.items():
        if key in cat_lower or cat_lower in key:
            return synonyms

    # Multi-word: try matching the last word (e.g. "software companies" -> "companies")
    words = cat_lower.split()
    if len(words) > 1:
        last_word = words[-1]
        if last_word in CATEGORY_SYNONYMS:
            base_synonyms = CATEGORY_SYNONYMS[last_word]
            return [category] + [f"{words[0]} {s}" for s in base_synonyms if s != last_word]

    return [category]


def build_location_scopes(location: str) -> list[str]:
    """Generate geographic scopes from a location string.
    
    Always includes the raw user-provided location as the primary scope.
    Does NOT substitute nearby or different cities.
    'London' -> ['London']
    'Eluru, Andhra Pradesh' -> ['Eluru', 'Eluru Andhra Pradesh', 'Eluru Andhra Pradesh India']
    'Toronto' -> ['Toronto', 'Toronto Canada']
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
