"""
url: /backend/app/adapters/google_places.py
About:
  Google Places API (New) adapter for ValLG. Implements the SourceAdapter
  interface for searching businesses via Google Places Text Search and
  Place Details endpoints. Handles rate limits, retries, and error handling.
  Supports the "Extract" stage only — no cleaning/dedup/validation here.
  Uses shared geo_config for all geographic data.
"""

import asyncio
import logging
from typing import Any

import httpx

from app.adapters.base import SourceAdapter
from app.geo import CITY_COORDS

logger = logging.getLogger(__name__)


class GooglePlacesAdapter(SourceAdapter):
    """Google Places API (New) adapter."""

    name = "google_places"
    display_name = "Google Places"

    # Rate limit: 100 QPS for new API (conservative default)
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    BASE_URL = "https://places.googleapis.com/v1"

    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)
        self.headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
        }

    async def search(
        self,
        query: str,
        location: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Search Google Places Text Search for businesses.

        Args:
            query: Search query (e.g., "IT companies in Bangalore")
            location: Optional location bias (e.g., "Bangalore, India")
            limit: Max results (max 20 per page for Places Text Search)
            offset: Not supported by Google Places API — ignored

        Returns:
            List of raw place records from Google Places API.
        """
        if not self.api_key:
            raise ValueError("Google Places API key not configured")

        # Build request body
        body: dict[str, Any] = {
            "textQuery": query,
            "maxResultCount": min(limit, 20),
            "languageCode": "en",
            "regionCode": "IN",
        }

        # Add location bias if provided
        if location:
            import re
            city_lower = location.split(",")[0].strip().lower()
            coords = CITY_COORDS.get(city_lower)
            lat, lng = coords if coords else (20.0, 78.0)
            body["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lng,
                    },
                    "radius": 50000.0,
                }
            }

        # Fields to request (minimize cost)
        fields = [
            "places.id",
            "places.displayName",
            "places.formattedAddress",
            "places.location",
            "places.rating",
            "places.userRatingCount",
            "places.websiteUri",
            "places.nationalPhoneNumber",
            "places.internationalPhoneNumber",
            "places.businessStatus",
            "places.types",
            "places.googleMapsUri",
        ]

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self.client.post(
                    f"{self.BASE_URL}/places:searchText",
                    headers=self.headers,
                    json=body,
                    params={",".join(["fields"]): ",".join(fields)},
                )

                if response.status_code == 429:
                    # Rate limited — back off and retry
                    wait = self.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Rate limited, waiting {wait}s")
                    await asyncio.sleep(wait)
                    continue

                response.raise_for_status()
                data = response.json()
                return data.get("places", [])

            except httpx.HTTPStatusError as e:
                logger.error(f"Google Places API error: {e.response.status_code}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
                    continue
                raise

        return []

    def normalize(self, raw_record: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize a Google Places record to RawRecord schema.

        Args:
            raw_record: Raw Google Places API response for a single place

        Returns:
            Normalized dict with source_record_id, raw_data fields.
        """
        place_id = raw_record.get("id", "")
        display_name = raw_record.get("displayName", {})
        location = raw_record.get("location", {})

        return {
            "source_record_id": place_id,
            "raw_data": {
                "place_id": place_id,
                "name": display_name.get("text", ""),
                "language": display_name.get("languageCode", "en"),
                "address": raw_record.get("formattedAddress", ""),
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "rating": raw_record.get("rating"),
                "review_count": raw_record.get("userRatingCount"),
                "website": raw_record.get("websiteUri"),
                "phone": raw_record.get("nationalPhoneNumber"),
                "phone_intl": raw_record.get("internationalPhoneNumber"),
                "business_status": raw_record.get("businessStatus"),
                "types": raw_record.get("types", []),
                "google_maps_url": raw_record.get("googleMapsUri"),
            },
        }

    async def health_check(self) -> bool:
        """
        Check if Google Places API is accessible with current key.

        Makes a minimal search request to verify API key validity.
        Returns True if successful, False otherwise.
        """
        if not self.api_key:
            return False

        try:
            body = {
                "textQuery": "test",
                "maxResultCount": 1,
            }
            response = await self.client.post(
                f"{self.BASE_URL}/places:searchText",
                headers=self.headers,
                json=body,
                params={"fields": "places.id"},
            )
            return response.status_code == 200

        except Exception:
            return False
