"""
url: /backend/app/adapters/openstreetmap.py
About:
  OpenStreetMap Overpass adapter for ValLG. Provides free, no-API-key
  business listing search via the Overpass API. Queries OSM for POIs
  matching the search term within a geographic area. Used as the
  default built-in source when no paid API keys are configured.
"""

import logging
import re
from typing import Any
from urllib.parse import urlencode

from app.adapters.base import SourceAdapter

logger = logging.getLogger(__name__)

OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.openstreetmap.ru/api/interpreter",
]
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Map common search terms to OSM tag queries
TAG_HINTS = {
    "restaurant": [("amenity", "restaurant")],
    "restaurants": [("amenity", "restaurant")],
    "cafe": [("amenity", "cafe")],
    "coffee": [("amenity", "cafe")],
    "coffee shop": [("amenity", "cafe")],
    "hotel": [("tourism", "hotel")],
    "hotels": [("tourism", "hotel")],
    "pharmacy": [("amenity", "pharmacy")],
    "pharmacies": [("amenity", "pharmacy")],
    "drugstore": [("amenity", "pharmacy")],
    "hospital": [("amenity", "hospital")],
    "hospitals": [("amenity", "hospital")],
    "clinic": [("amenity", "clinic")],
    "clinics": [("amenity", "clinic")],
    "dental": [("amenity", "dentist")],
    "dentist": [("amenity", "dentist")],
    "dentists": [("amenity", "dentist")],
    "doctor": [("amenity", "doctor")],
    "doctors": [("amenity", "doctor")],
    "gym": [("leisure", "fitness_centre")],
    "gyms": [("leisure", "fitness_centre")],
    "fitness": [("leisure", "fitness_centre")],
    "fitness centre": [("leisure", "fitness_centre")],
    "fitness center": [("leisure", "fitness_centre")],
    "health club": [("leisure", "fitness_centre")],
    "shop": [("shop", "~.")],
    "store": [("shop", "~.")],
    "stores": [("shop", "~.")],
    "shops": [("shop", "~.")],
    "bank": [("amenity", "bank")],
    "banks": [("amenity", "bank")],
    "atm": [("amenity", "atm")],
    "atms": [("amenity", "atm")],
    "school": [("amenity", "school")],
    "schools": [("amenity", "school")],
    "college": [("amenity", "college")],
    "colleges": [("amenity", "college")],
    "university": [("amenity", "university")],
    "office": [("office", "~.")],
    "offices": [("office", "~.")],
    "it": [("office", "IT")],
    "it company": [("office", "IT")],
    "it companies": [("office", "IT")],
    "technology": [("office", "IT")],
    "tech": [("office", "IT")],
    "software": [("office", "IT")],
    "software company": [("office", "IT")],
    "software companies": [("office", "IT")],
    "startup": [("office", "IT")],
    "startups": [("office", "IT")],
    "real estate": [("office", "estate_agent")],
    "real estate agent": [("office", "estate_agent")],
    "legal": [("office", "lawyer")],
    "lawyer": [("office", "lawyer")],
    "lawyers": [("office", "lawyer")],
    "attorney": [("office", "lawyer")],
    "advocate": [("office", "lawyer")],
    "accounting": [("office", "accountant")],
    "accountant": [("office", "accountant")],
    "ca": [("office", "accountant")],
    "spa": [("amenity", "spa")],
    "spas": [("amenity", "spa")],
    "salon": [("shop", "beauty")],
    "salons": [("shop", "beauty")],
    "beauty": [("shop", "beauty")],
    "beauty salon": [("shop", "beauty")],
    "beauty parlor": [("shop", "beauty")],
    "electronics": [("shop", "electronics")],
    "electronic": [("shop", "electronics")],
    "grocery": [("shop", "supermarket")],
    "grocery store": [("shop", "supermarket")],
    "supermarket": [("shop", "supermarket")],
    "supermarkets": [("shop", "supermarket")],
    "pet": [("shop", "pet")],
    "pet shop": [("shop", "pet")],
    "pet store": [("shop", "pet")],
    "car": [("shop", "car")],
    "automobile": [("shop", "car")],
    "vehicle": [("shop", "car")],
    "auto": [("shop", "car")],
    "clothing": [("shop", "clothes")],
    "clothes": [("shop", "clothes")],
    "fashion": [("shop", "clothes")],
    "apparel": [("shop", "clothes")],
    "manufacturer": [("craft", "manufacture")],
    "manufacturers": [("craft", "manufacture")],
    "factory": [("craft", "manufacture")],
    "factories": [("craft", "manufacture")],
    "bakery": [("amenity", "bakery")],
    "bar": [("amenity", "bar")],
    "pub": [("amenity", "pub")],
    "nightclub": [("amenity", "nightclub")],
    "fuel": [("amenity", "fuel")],
    "gas station": [("amenity", "fuel")],
    "parking": [("amenity", "parking")],
    "cinema": [("amenity", "cinema")],
    "theatre": [("amenity", "theatre")],
    "theater": [("amenity", "theatre")],
    "library": [("amenity", "library")],
    "community centre": [("amenity", "community_centre")],
    "community center": [("amenity", "community_centre")],
    "marketplace": [("amenity", "marketplace")],
    "market": [("amenity", "marketplace")],
    "courier": [("office", "courier")],
    "logistics": [("office", "logistics")],
    "travel": [("office", "travel_agent")],
    "travel agency": [("office", "travel_agent")],
    "insurance": [("office", "insurance")],
    "consulting": [("office", "consulting")],
    "consultancy": [("office", "consulting")],
}


class OpenStreetMapAdapter(SourceAdapter):
    """Searches OpenStreetMap via the Overpass API. No API key required."""

    name = "openstreetmap"
    display_name = "OpenStreetMap (Free)"

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=None)

    async def _geocode(self, location: str) -> tuple[float, float, float] | None:
        """Geocode a location string to (lat, lon, radius_meters).
        
        First checks CITY_COORDS for known cities to avoid Nominatim rate limits.
        Falls back to Nominatim API with retry logic.
        """
        from app.geo import CITY_COORDS, get_coords_for_city

        # Check known cities first (no API call needed)
        coords = get_coords_for_city(location.lower().strip())
        if coords:
            lat, lon = coords
            return lat, lon, 15000  # 15km default radius for known cities

        import asyncio as _asyncio
        for attempt in range(3):
            try:
                resp = await self.client.get(
                    NOMINATIM_URL,
                    params={"q": location, "format": "json", "limit": 1},
                    headers={"User-Agent": "ValLG/1.0 (leadgen-app)"},
                )
                if resp.status_code == 429:
                    wait = 2 * (attempt + 1)
                    logger.warning(f"Nominatim rate limited, waiting {wait}s...")
                    await _asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                results = resp.json()
                if not results:
                    return None
                r = results[0]
                lat = float(r["lat"])
                lon = float(r["lon"])
                if "boundingbox" in r:
                    bb = [float(x) for x in r["boundingbox"]]
                    lat_span = abs(bb[2] - bb[0])
                    lon_span = abs(bb[3] - bb[1])
                    radius = max(lat_span, lon_span) * 111_000 / 2
                    radius = max(radius, 5000)
                    radius = min(radius, 50000)
                else:
                    radius = 10000
                return lat, lon, radius
            except Exception as e:
                if attempt == 2:
                    logger.error(f"Geocode failed after 3 attempts: {e}")
                    return None
                await _asyncio.sleep(2 * (attempt + 1))
        return None

    def _build_tag_groups(self, query: str) -> list[list[tuple[str, str]]]:
        """Build Overpass tag groups from the user's query.
        
        The user's query text IS the search. For known categories, we use
        structured OSM tags (fast, precise). For unknown categories, we use
        name-based search (flexible, works for any category).
        """
        import re
        q_lower = query.lower().strip()

        # Remove location words if present
        for sep in [" in ", " near ", " around ", " at ", " of "]:
            if sep in q_lower:
                q_lower = q_lower.split(sep, 1)[0].strip()
                break

        tag_groups = []

        # Check if this is a known category with structured OSM tags
        if q_lower in TAG_HINTS:
            # Known category: use structured tags ONLY (no name filter)
            # This is fast and returns all matching OSM entities
            tag_groups.append(TAG_HINTS[q_lower])
        else:
            # Unknown category: use name-based search
            # This works for ANY category without predefined mappings
            name_regex = f".*{re.escape(q_lower)}.*"
            tag_groups.append([("name", name_regex)])

        return tag_groups

    def _build_tags(self, query: str) -> list[tuple[str, str]]:
        """Backward-compatible method: returns flattened tags for testing."""
        tag_groups = self._build_tag_groups(query)
        # Flatten all groups
        flat_tags = []
        for group in tag_groups:
            flat_tags.extend(group)
        return flat_tags

    def _to_posix_case_insensitive(self, pattern: str) -> str:
        """Convert a simple string pattern to POSIX case-insensitive regex.
        
        Converts 'spa' to '[Ss][Pp][Aa]' and '.*spa.*' to '.*[Ss][Pp][Aa].*'
        """
        import re
        # Replace each alphabetic character with [upper][lower] pair
        def replace_char(match):
            char = match.group(0)
            if char.isalpha():
                return f'[{char.upper()}{char.lower()}]'
            return char
        
        # Apply to alphabetic sequences, preserve regex metacharacters
        result = ""
        i = 0
        while i < len(pattern):
            if pattern[i].isalpha():
                # Find consecutive alphabetic characters
                j = i
                while j < len(pattern) and pattern[j].isalpha():
                    j += 1
                alpha_seq = pattern[i:j]
                for ch in alpha_seq:
                    result += f'[{ch.upper()}{ch.lower()}]'
                i = j
            else:
                result += pattern[i]
                i += 1
        return result

    def _build_overpass_query(self, tag_groups: list[list[tuple[str, str]]], lat: float, lon: float, radius: int) -> str:
        """Build Overpass QL query from tag groups using UNION for OR logic."""
        subqueries = []
        for group in tag_groups:
            tag_filters = ""
            for k, v in group:
                # Detect regex patterns: contains regex metacharacters
                is_regex = any(c in v for c in ".*+?^$[]()|{}")
                if is_regex:
                    # Convert to POSIX case-insensitive regex
                    posix_pattern = self._to_posix_case_insensitive(v)
                    tag_filters += f'["{k}"~"{posix_pattern}"]'
                elif v.startswith("~"):
                    # Explicit regex marker (legacy)
                    posix_pattern = self._to_posix_case_insensitive(v[1:])
                    tag_filters += f'["{k}"~"{posix_pattern}"]'
                else:
                    # Exact match
                    tag_filters += f'["{k}"="{v}"]'
            
            subqueries.append(f"""
              node{tag_filters}(around:{radius},{lat},{lon});
              way{tag_filters}(around:{radius},{lat},{lon});
              relation{tag_filters}(around:{radius},{lat},{lon});
            """)
        
        union_query = "\n".join(subqueries)
        overpass_ql = f"""
        [out:json][timeout:60];
        (
          {union_query}
        );
        out center body;
        """
        return overpass_ql

    async def search(
        self,
        query: str,
        location: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Search OSM for businesses matching query in the given location."""
        if not location:
            logger.warning("OpenStreetMap adapter requires a location")
            return []

        geo = await self._geocode(location)
        if geo is None:
            logger.warning(f"Could not geocode location: {location}")
            return []

        lat, lon, radius = geo
        tag_groups = self._build_tag_groups(query)
        overpass_ql = self._build_overpass_query(tag_groups, lat, lon, radius)

        # Try multiple Overpass mirrors for reliability
        data = None
        for mirror_url in OVERPASS_MIRRORS:
            try:
                resp = await self.client.post(
                    mirror_url,
                    data={"data": overpass_ql},
                    headers={"User-Agent": "ValLG/1.0"},
                    timeout=60.0,
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except Exception as e:
                logger.warning(f"Overpass mirror {mirror_url} failed: {e}")
                continue

        if data is None:
            logger.error("All Overpass mirrors failed")
            return []

        elements = data.get("elements", [])

        # Convert OSM elements to our raw record format with deduplication
        records = []
        seen_ids = set()
        for el in elements:
            tags_data = el.get("tags", {})
            name = tags_data.get("name", "")
            if not name:
                continue

            # Deduplicate by OSM ID + type
            osm_id = el.get("id")
            osm_type = el.get("type")
            dedup_key = f"{osm_type}:{osm_id}"
            if dedup_key in seen_ids:
                continue
            seen_ids.add(dedup_key)

            # Get coordinates
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lon = el.get("lon") or el.get("center", {}).get("lon")

            # Build address from OSM tags
            addr_parts = []
            for key in ["addr:housenumber", "addr:street", "addr:city", "addr:state", "addr:postcode"]:
                if key in tags_data:
                    addr_parts.append(tags_data[key])
            address = ", ".join(addr_parts) if addr_parts else ""

            record = {
                "osm_id": osm_id,
                "osm_type": osm_type,
                "name": name,
                "address": address,
                "phone": tags_data.get("phone") or tags_data.get("contact:phone"),
                "website": tags_data.get("website") or tags_data.get("contact:website"),
                "email": tags_data.get("email") or tags_data.get("contact:email"),
                "lat": el_lat,
                "lon": el_lon,
                "category": tags_data.get("amenity") or tags_data.get("shop") or tags_data.get("office") or tags_data.get("tourism") or "",
                "opening_hours": tags_data.get("opening_hours"),
                "all_tags": tags_data,
            }
            records.append(record)
            if len(records) >= limit:
                break

        return records

    def normalize(self, raw_record: dict[str, Any]) -> dict[str, Any]:
        """Normalize an OSM element to the common RawRecord schema."""
        all_tags = raw_record.get("all_tags", {})
        city = all_tags.get("addr:city")
        state = all_tags.get("addr:state")
        pin_code = all_tags.get("addr:postcode")
        return {
            "source_record_id": f"osm_{raw_record.get('osm_type', 'node')}_{raw_record.get('osm_id', '')}",
            "raw_data": {
                "name": raw_record.get("name"),
                "address": raw_record.get("address"),
                "city": city,
                "state": state,
                "pin_code": pin_code,
                "phone": raw_record.get("phone"),
                "website": raw_record.get("website"),
                "email": raw_record.get("email"),
                "industry": raw_record.get("category"),
                "latitude": raw_record.get("lat"),
                "longitude": raw_record.get("lon"),
                "rating": None,
                "reviews_count": None,
                "opening_hours": raw_record.get("opening_hours"),
                "maps_url": None,
                "source_url": f"https://www.openstreetmap.org/{raw_record.get('osm_type', 'node')}/{raw_record.get('osm_id', '')}",
                "metadata": {
                    "extraction_method": "openstreetmap",
                    "osm_type": raw_record.get("osm_type"),
                    "osm_id": raw_record.get("osm_id"),
                    "all_tags": raw_record.get("all_tags", {}),
                },
            },
        }

    async def health_check(self) -> bool:
        """Check if Overpass API is reachable."""
        for mirror_url in OVERPASS_MIRRORS:
            try:
                resp = await self.client.get(
                    mirror_url.replace("/interpreter", "/status"),
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return True
            except Exception:
                continue
        return False
