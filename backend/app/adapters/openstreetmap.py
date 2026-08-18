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
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Map common search terms to OSM tag queries
TAG_HINTS = {
    "restaurant": [("amenity", "restaurant")],
    "cafe": [("amenity", "cafe")],
    "coffee": [("amenity", "cafe")],
    "hotel": [("tourism", "hotel")],
    "pharmacy": [("amenity", "pharmacy")],
    "hospital": [("amenity", "hospital")],
    "clinic": [("amenity", "clinic")],
    "gym": [("leisure", "fitness_centre")],
    "fitness": [("leisure", "fitness_centre")],
    "shop": [("shop", "~.")],
    "store": [("shop", "~.")],
    "bank": [("amenity", "bank")],
    "atm": [("amenity", "atm")],
    "school": [("amenity", "school")],
    "college": [("amenity", "college")],
    "office": [("office", "~.")],
    "IT": [("office", "IT")],
    "technology": [("office", "IT")],
    "software": [("office", "IT")],
    "real estate": [("office", "estate_agent")],
    "legal": [("office", "lawyer")],
    "lawyer": [("office", "lawyer")],
    "accounting": [("office", "accountant")],
    "spa": [("amenity", "spa")],
    "salon": [("shop", "beauty")],
    "beauty": [("shop", "beauty")],
    "electronics": [("shop", "electronics")],
    "grocery": [("shop", "supermarket")],
    "supermarket": [("shop", "supermarket")],
    "pet": [("shop", "pet")],
    "car": [("shop", "car")],
    "automobile": [("shop", "car")],
    "clothing": [("shop", "clothes")],
    "fashion": [("shop", "clothes")],
    "startup": [("office", "IT")],
    "manufacturer": [("craft", "manufacture")],
    "factory": [("craft", "manufacture")],
    "IT": [("office", "IT")],
    "technology": [("office", "IT")],
    "software": [("office", "IT")],
}


class OpenStreetMapAdapter(SourceAdapter):
    """Searches OpenStreetMap via the Overpass API. No API key required."""

    name = "openstreetmap"
    display_name = "OpenStreetMap (Free)"

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=None)

    async def _geocode(self, location: str) -> tuple[float, float, float] | None:
        """Geocode a location string to (lat, lon, radius_meters)."""
        resp = await self.client.get(
            NOMINATIM_URL,
            params={"q": location, "format": "json", "limit": 1},
            headers={"User-Agent": "ValLG/1.0 (leadgen-app)"},
        )
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None
        r = results[0]
        lat = float(r["lat"])
        lon = float(r["lon"])
        # Use bounding box to estimate radius, default 10km
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

    def _build_tags(self, query: str) -> list[tuple[str, str]]:
        """Determine OSM tags from the search query."""
        q_lower = query.lower().strip()

        # Check exact matches first
        for key, tags in TAG_HINTS.items():
            if key in q_lower:
                return tags

        # Fallback: search by name with regex match on the query
        return [("name", f"(?i){re.escape(query)}")]

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
        tags = self._build_tags(query)

        # Build Overpass QL query
        tag_filters = "".join(
            f'["{k}"="{v}"]' if not v.startswith("~") else f'["{k}"~"{v[1:]}"]'
            for k, v in tags
        )

        overpass_ql = f"""
        [out:json][timeout:30];
        (
          node{tag_filters}(around:{radius},{lat},{lon});
          way{tag_filters}(around:{radius},{lat},{lon});
          relation{tag_filters}(around:{radius},{lat},{lon});
        );
        out center body;
        """

        # Try multiple Overpass mirrors for reliability
        data = None
        for mirror_url in OVERPASS_MIRRORS:
            try:
                resp = await self.client.get(
                    mirror_url,
                    params={"data": overpass_ql},
                    headers={"User-Agent": "ValLG/1.0"},
                    timeout=30.0,
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

        elements = data.get("elements", [])[:limit]

        # Convert OSM elements to our raw record format
        records = []
        for el in elements:
            tags_data = el.get("tags", {})
            name = tags_data.get("name", "")
            if not name:
                continue

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
                "osm_id": el.get("id"),
                "osm_type": el.get("type"),
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

        return records

    def normalize(self, raw_record: dict[str, Any]) -> dict[str, Any]:
        """Normalize an OSM element to the common RawRecord schema."""
        return {
            "source_record_id": f"osm_{raw_record.get('osm_type', 'node')}_{raw_record.get('osm_id', '')}",
            "raw_data": {
                "name": raw_record.get("name"),
                "address": raw_record.get("address"),
                "city": None,
                "state": None,
                "pin_code": None,
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
