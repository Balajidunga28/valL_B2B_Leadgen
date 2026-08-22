"""
url: /backend/app/adapters/openstreetmap.py
About:
  OpenStreetMap Overpass adapter for ValLG. Provides free, no-API-key
  business listing search via the Overpass API. Queries OSM for POIs
  matching the search term within a geographic area. Used as the
  default built-in source when no paid API keys are configured.
"""

import asyncio
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

_GEOCODE_CACHE: dict[str, tuple[float, float, float] | None] = {}




class OpenStreetMapAdapter(SourceAdapter):
    """Searches OpenStreetMap via the Overpass API. No API key required."""

    name = "openstreetmap"
    display_name = "OpenStreetMap (Free)"

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=None)

    async def _geocode(self, location: str) -> tuple[float, float, float] | None:
        """Geocode a location string to (lat, lon, radius_meters).
        
        First checks CITY_COORDS for known cities to avoid Nominatim rate limits.
        Falls back to Nominatim API with retry logic. Uses in-memory cache.
        """
        from app.geo import CITY_COORDS, get_coords_for_city

        loc_key = location.lower().strip()
        
        # Check cache first
        if loc_key in _GEOCODE_CACHE:
            return _GEOCODE_CACHE[loc_key]

        # Check known cities first (no API call needed)
        coords = get_coords_for_city(loc_key)
        if coords:
            lat, lon = coords
            result = (lat, lon, 15000)
            _GEOCODE_CACHE[loc_key] = result
            return result

        # Single attempt with shorter timeout for Nominatim
        try:
            resp = await self.client.get(
                NOMINATIM_URL,
                params={"q": location, "format": "json", "limit": 1},
                headers={"User-Agent": "ValLG/1.0 (leadgen-app)"},
                timeout=10.0,
            )
            if resp.status_code == 429:
                logger.warning("Nominatim rate limited")
                return None
            resp.raise_for_status()
            results = resp.json()
            if not results:
                _GEOCODE_CACHE[loc_key] = None
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
            result = (lat, lon, radius)
            _GEOCODE_CACHE[loc_key] = result
            return result
        except Exception as e:
            logger.warning(f"Geocode failed for '{location}': {e}")
            _GEOCODE_CACHE[loc_key] = None
            return None

    def _build_tag_groups(self, query: str) -> list[list[tuple[str, str]]]:
        """Build Overpass tag groups from the user's query.
        
        Always uses name-based search — the user's query text goes directly
        to Overpass as a case-insensitive regex pattern. No predefined
        category mappings or templates.
        """
        q_lower = query.lower().strip()

        # Remove location words if present
        for sep in [" in ", " near ", " around ", " at ", " of "]:
            if sep in q_lower:
                q_lower = q_lower.split(sep, 1)[0].strip()
                break

        tag_groups = []

        # Always use name-based search — the query IS the search term
        tag_groups.append([("name", q_lower)])

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
        Also handles common singular/plural: 'spas' -> '[Ss][Pp][Aa][Ss]?'
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
                # Handle trailing 's' for plural -> make it optional
                if len(alpha_seq) > 3 and alpha_seq.endswith('s'):
                    for ch in alpha_seq[:-1]:
                        result += f'[{ch.upper()}{ch.lower()}]'
                    result += f'[{alpha_seq[-1].upper()}{alpha_seq[-1].lower()}]?'
                else:
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
            # Group multiple values for the same key into a single regex with OR
            # e.g., [("name", "salon"), ("name", "salons")] -> ["name"~"pattern1|pattern2"]
            key_values: dict[str, list[str]] = {}
            for k, v in group:
                key_values.setdefault(k, []).append(v)
            
            tag_filters = ""
            for key, values in key_values.items():
                if key == "name":
                    # Combine multiple name patterns into single regex with OR
                    posix_patterns = [self._to_posix_case_insensitive(v) for v in values]
                    combined = "|".join(posix_patterns)
                    tag_filters += f'["{key}"~"{combined}"]'
                elif len(values) == 1:
                    v = values[0]
                    is_regex = any(c in v for c in ".*+?^$[]()|{}")
                    if is_regex:
                        posix_pattern = self._to_posix_case_insensitive(v)
                        tag_filters += f'["{key}"~"{posix_pattern}"]'
                    elif v.startswith("~"):
                        posix_pattern = self._to_posix_case_insensitive(v[1:])
                        tag_filters += f'["{key}"~"{posix_pattern}"]'
                    else:
                        tag_filters += f'["{key}"="{v}"]'
                else:
                    # Multiple values for non-name key: combine with OR
                    posix_patterns = [self._to_posix_case_insensitive(v) for v in values]
                    combined = "|".join(posix_patterns)
                    tag_filters += f'["{key}"~"{combined}"]'
            
            subqueries.append(f"""
              node{tag_filters}(around:{radius},{lat},{lon});
              way{tag_filters}(around:{radius},{lat},{lon});
              relation{tag_filters}(around:{radius},{lat},{lon});
            """)
        
        union_query = "\n".join(subqueries)
        overpass_ql = f"""
        [out:json][timeout:30];
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

        # Try mirrors concurrently, return first successful response
        async def try_mirror(mirror_url: str):
            try:
                resp = await self.client.post(
                    mirror_url,
                    data={"data": overpass_ql},
                    headers={"User-Agent": "ValLG/1.0"},
                    timeout=45.0,
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.debug(f"Overpass mirror {mirror_url} failed: {e}")
                return None

        # Use asyncio.wait with FIRST_COMPLETED to get fastest successful response
        tasks = {asyncio.create_task(try_mirror(url)): url for url in OVERPASS_MIRRORS}
        
        data = None
        while tasks:
            done, tasks = await asyncio.wait(tasks, timeout=50.0, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                try:
                    result = task.result()
                    if isinstance(result, dict) and result is not None:
                        data = result
                        # Cancel remaining tasks
                        for t in tasks:
                            t.cancel()
                        tasks = {}
                        break
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass
            if data is not None:
                break
        
        # If no result and timed out, cancel all
        if data is None:
            for t in tasks:
                t.cancel()
            logger.error("All Overpass mirrors failed or timed out")
            return []

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
