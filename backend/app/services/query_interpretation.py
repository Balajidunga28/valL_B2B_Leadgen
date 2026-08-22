"""
url: /backend/app/services/query_interpretation.py
About:
  Natural language query interpretation for Maps-based Discovery.
  Extracts category intent, location, and meaningful qualifiers from
  free-form user queries. Generates search variations for broad retrieval.
"""

import re
from dataclasses import dataclass
from typing import Optional

from app.geo import CITY_COORDS, INDIAN_STATES_LOWER, build_location_scopes


@dataclass
class InterpretedQuery:
    """Result of query interpretation."""
    original_query: str
    category: str
    location: Optional[str]
    qualifiers: list[str]
    search_variations: list[str]
    location_scopes: list[str]


# Prepositions that typically introduce location
LOCATION_PREPOSITIONS = [
    " in ", " near ", " around ", " at ", " from ", " within ",
    " close to ", " nearby ", " outside ", " inside "
]

# Patterns that might indicate category qualifiers (preserve these)
QUALIFIER_PATTERNS = [
    r"\b(indian|chinese|italian|mexican|japanese|thai|korean|mediterranean|american)\b",
    r"\b(vegetarian|vegan|halal|kosher|organic|gluten.free)\b",
    r"\b(luxury|budget|cheap|expensive|premium|affordable)\b",
    r"\b(family|kid.friendly|romantic|business|casual|fine.dining)\b",
    r"\b(24.hour|24/7|late.night|early.morning|open.now)\b",
    r"\b(top.rated|best|popular|recommended|highly.rated)\b",
    r"\b(delivery|takeout|take.away|dine.in|outdoor.seating)\b",
    r"\b(private|public|government|nonprofit|charity)\b",
    r"\b(startup|small.business|enterprise|corporate|multinational)\b",
    r"\b(digital|online|remote|onsite|hybrid)\b",
    r"\b(certified|licensed|accredited|registered|approved)\b",
]


def _extract_location_from_query(query: str) -> Optional[str]:
    """Extract location from query using preposition patterns and comma separation."""
    q = query.strip()
    
    # Check for comma-separated location (e.g., "restaurants, Johannesburg")
    if "," in q:
        parts = q.split(",", 1)
        if len(parts) == 2:
            loc = parts[1].strip()
            # Clean up trailing punctuation
            loc = re.sub(r"[.;:]+$", "", loc)
            if loc and len(loc) > 1:
                return loc
    
    # Check for prepositions
    for prep in LOCATION_PREPOSITIONS:
        idx = q.lower().find(prep)
        if idx != -1:
            loc = q[idx + len(prep):].strip()
            if loc:
                # Clean up trailing punctuation
                loc = re.sub(r"[.,;:]+$", "", loc)
                return loc
    
    # Check if word(s) is a known city (e.g., "restaurants Johannesburg" or "Johannesburg restaurants")
    words = q.split()
    if len(words) >= 2:
        # Try multi-word city names at end
        for i in range(len(words) - 1, 0, -1):
            potential_loc = " ".join(words[i:])
            if potential_loc.lower() in CITY_COORDS:
                return potential_loc
        # Try single word at end
        if words[-1].lower() in CITY_COORDS:
            return words[-1]
        # Try multi-word city names at beginning
        for i in range(1, len(words)):
            potential_loc = " ".join(words[:i])
            if potential_loc.lower() in CITY_COORDS:
                return potential_loc
        # Try single word at beginning
        if words[0].lower() in CITY_COORDS:
            return words[0]
    
    return None


def _extract_category_from_query(query: str) -> str:
    """Extract the main category from query, preserving qualifiers."""
    q = query.strip()
    
    # Handle comma-separated format (e.g., "restaurants, Johannesburg")
    if "," in q:
        parts = q.split(",", 1)
        category = parts[0].strip()
        if category:
            return category
    
    # Handle prepositions
    for prep in LOCATION_PREPOSITIONS:
        idx = q.lower().find(prep)
        if idx != -1:
            return q[:idx].strip()
    
    words = q.split()
    if len(words) >= 2:
        # Handle location at end (e.g., "restaurants Johannesburg")
        for i in range(len(words) - 1, 0, -1):
            potential_loc = " ".join(words[i:])
            if potential_loc.lower() in CITY_COORDS:
                return " ".join(words[:i])
        if words[-1].lower() in CITY_COORDS:
            return " ".join(words[:-1])
        
        # Handle location at beginning (e.g., "Johannesburg restaurants")
        for i in range(1, len(words)):
            potential_loc = " ".join(words[:i])
            if potential_loc.lower() in CITY_COORDS:
                return " ".join(words[i:])
        if words[0].lower() in CITY_COORDS:
            return " ".join(words[1:])
    
    return q.strip()


def _extract_qualifiers(category: str) -> list[str]:
    """Extract meaningful qualifiers from the category text."""
    qualifiers = []
    cat_lower = category.lower()
    
    for pattern in QUALIFIER_PATTERNS:
        matches = re.findall(pattern, cat_lower, re.IGNORECASE)
        qualifiers.extend(matches)
    
    # Deduplicate while preserving order
    seen = set()
    unique_qualifiers = []
    for q in qualifiers:
        q_lower = q.lower()
        if q_lower not in seen:
            seen.add(q_lower)
            unique_qualifiers.append(q)
    
    return unique_qualifiers


def _normalize_category(category: str, qualifiers: list[str]) -> str:
    """Normalize the category by removing location words but keeping qualifiers."""
    cat = category.strip()
    
    # Remove trailing prepositional phrases that might be location-like
    for prep in LOCATION_PREPOSITIONS:
        idx = cat.lower().find(prep)
        if idx != -1:
            cat = cat[:idx].strip()
    
    # Remove standalone city/state names that might be at the end
    words = cat.split()
    while words and words[-1].lower() in INDIAN_STATES_LOWER:
        words.pop()
    
    # Check if last word is a known city
    if words and words[-1].lower() in CITY_COORDS:
        # Only remove if it's truly a location suffix, not part of business name
        # e.g., "Bangalore IT companies" -> keep "IT companies"
        # But "restaurants Bangalore" -> "restaurants"
        # This is heuristic: if category starts with business type, keep it
        pass  # We'll be conservative and not auto-remove
    
    return " ".join(words).strip()


def _generate_search_variations(category: str, location: Optional[str], qualifiers: list[str]) -> list[str]:
    """Generate search query variations for broad retrieval."""
    variations = []
    
    # Base category already has qualifiers embedded
    base_category = category
    
    # Variation 1: Category + location (various orders)
    if location:
        variations.append(f"{base_category} in {location}")
        variations.append(f"{base_category} {location}")
        variations.append(f"{location} {base_category}")
    
    # Variation 2: Just category (broad)
    variations.append(base_category)
    
    # Variation 3: Singular/plural variations of main category word
    cat_words = base_category.split()
    if cat_words:
        main_cat = cat_words[0]
        # Only do singular/plural if it's a common business type word
        # and not an acronym like "IT" or a proper adjective like "Indian"
        if (len(main_cat) > 2 
            and not main_cat.isupper()
            and main_cat[0].islower()):  # Only lowercase words (not proper nouns)
            if main_cat.endswith("s") and not main_cat.endswith("ss") and len(main_cat) > 3:
                singular = main_cat[:-1]
                if singular and len(singular) > 2:
                    variations.append(base_category.replace(main_cat, singular, 1))
            elif not main_cat.endswith("s"):
                plural = main_cat + "s"
                variations.append(base_category.replace(main_cat, plural, 1))
    
    # Deduplicate
    seen = set()
    unique = []
    for v in variations:
        v_clean = v.strip().lower()
        if v_clean and v_clean not in seen:
            seen.add(v_clean)
            unique.append(v.strip())
    
    return unique


def interpret_query(query: str, explicit_location: Optional[str] = None) -> InterpretedQuery:
    """
    Interpret a natural language search query.
    
    Args:
        query: User's raw search query
        explicit_location: Optional location from separate location field
        
    Returns:
        InterpretedQuery with category, location, qualifiers, and search variations
    """
    original = query.strip()
    
    # Extract location (explicit location takes precedence)
    location = explicit_location
    if not location:
        location = _extract_location_from_query(original)
    
    # Extract category
    category = _extract_category_from_query(original)
    
    # Extract qualifiers from category
    qualifiers = _extract_qualifiers(category)
    
    # Normalize category (remove location artifacts but keep qualifiers)
    normalized_category = _normalize_category(category, qualifiers)
    
    # Generate search variations
    search_variations = _generate_search_variations(normalized_category, location, qualifiers)
    
    # Add original query as first variation (most specific intent)
    if original.lower() not in [v.lower() for v in search_variations]:
        search_variations.insert(0, original)
    
    # Build location scopes for adapters
    location_scopes = build_location_scopes(location) if location else [""]
    
    return InterpretedQuery(
        original_query=original,
        category=normalized_category,
        location=location,
        qualifiers=qualifiers,
        search_variations=search_variations,
        location_scopes=location_scopes,
    )


def get_primary_search_query(interpreted: InterpretedQuery) -> str:
    """Get the primary search query to use (most specific variation)."""
    return interpreted.search_variations[0] if interpreted.search_variations else interpreted.original_query


def get_all_search_queries(interpreted: InterpretedQuery, max_variations: int = 5) -> list[str]:
    """Get all search queries to try, limited to max_variations."""
    return interpreted.search_variations[:max_variations]