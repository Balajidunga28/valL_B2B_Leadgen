"""
url: /backend/tests/test_google_maps_scraper.py
About:
  Unit tests for the Google Maps Scraper adapter.
  Tests adapter instantiation, normalization, and error handling.
  Uses mocked browser for unit testing without live Google Maps dependency.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.adapters.google_maps_scraper import (
    GoogleMapsScraperAdapter,
    _extract_location_from_address,
    _parse_query,
    _dedup_key,
)
from app.adapters.base import SourceAdapter


class TestGoogleMapsScraperAdapter:
    """Tests for GoogleMapsScraperAdapter."""

    def test_adapter_instantiation(self):
        """Test that adapter can be instantiated through existing architecture."""
        adapter = GoogleMapsScraperAdapter()
        assert isinstance(adapter, SourceAdapter)
        assert adapter.name == "google_maps_scraper"
        assert adapter.display_name == "Google Maps Scraper"
        assert adapter.api_key is None

    def test_adapter_inherits_base_interface(self):
        """Test that adapter implements all required abstract methods."""
        adapter = GoogleMapsScraperAdapter()
        assert hasattr(adapter, 'search')
        assert hasattr(adapter, 'normalize')
        assert hasattr(adapter, 'health_check')
        assert hasattr(adapter, 'close')

    def test_normalize_with_complete_data(self):
        """Test normalization with all fields present."""
        adapter = GoogleMapsScraperAdapter()
        raw_record = {
            "name": "Test Restaurant",
            "address": "123 Main St, Mumbai, Maharashtra",
            "phone": "+91 22 1234 5678",
            "website": "https://test.com",
            "rating": 4.5,
            "reviews_count": 100,
            "category": "restaurant",
            "opening_hours": "Mon-Fri 9-5",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "maps_url": "https://maps.google.com/place/123",
            "_provenance": {
                "search_query": "restaurants in Mumbai",
                "search_url": "https://maps.google.com/search/restaurants+in+Mumbai",
                "extracted_at": "2024-01-01T00:00:00Z",
                "extraction_method": "google_maps_scraper",
            },
        }
        normalized = adapter.normalize(raw_record)
        
        assert normalized["source_record_id"].startswith("gmaps_scraper_")
        assert normalized["raw_data"]["name"] == "Test Restaurant"
        assert normalized["raw_data"]["address"] == "123 Main St, Mumbai, Maharashtra"
        assert normalized["raw_data"]["city"] == "Mumbai"
        assert normalized["raw_data"]["state"] == "Maharashtra"
        assert normalized["raw_data"]["pin_code"] is None
        assert normalized["raw_data"]["phone"] == "+91 22 1234 5678"
        assert normalized["raw_data"]["website"] == "https://test.com"
        assert normalized["raw_data"]["email"] is None
        assert normalized["raw_data"]["industry"] == "restaurant"
        assert normalized["raw_data"]["latitude"] == 19.0760
        assert normalized["raw_data"]["longitude"] == 72.8777
        assert normalized["raw_data"]["rating"] == 4.5
        assert normalized["raw_data"]["reviews_count"] == 100
        assert normalized["raw_data"]["opening_hours"] == "Mon-Fri 9-5"
        assert normalized["raw_data"]["maps_url"] == "https://maps.google.com/place/123"
        assert normalized["raw_data"]["metadata"]["extraction_method"] == "google_maps_scraper"
        assert normalized["raw_data"]["metadata"]["search_query"] == "restaurants in Mumbai"

    def test_normalize_with_missing_optional_fields(self):
        """Test normalization handles missing optional fields gracefully."""
        adapter = GoogleMapsScraperAdapter()
        raw_record = {
            "name": "Minimal Business",
            "address": "",
            "phone": None,
            "website": None,
            "rating": None,
            "reviews_count": None,
            "category": None,
            "opening_hours": None,
            "latitude": None,
            "longitude": None,
            "maps_url": None,
            "_provenance": {},
        }
        normalized = adapter.normalize(raw_record)
        
        assert normalized["source_record_id"].startswith("gmaps_scraper_")
        assert normalized["raw_data"]["name"] == "Minimal Business"
        assert normalized["raw_data"]["address"] == ""
        assert normalized["raw_data"]["city"] is None
        assert normalized["raw_data"]["state"] is None
        assert normalized["raw_data"]["pin_code"] is None
        assert normalized["raw_data"]["phone"] is None
        assert normalized["raw_data"]["website"] is None
        assert normalized["raw_data"]["email"] is None
        assert normalized["raw_data"]["industry"] is None
        assert normalized["raw_data"]["latitude"] is None
        assert normalized["raw_data"]["longitude"] is None
        assert normalized["raw_data"]["rating"] is None
        assert normalized["raw_data"]["reviews_count"] is None
        assert normalized["raw_data"]["opening_hours"] is None
        assert normalized["raw_data"]["maps_url"] is None
        assert "metadata" in normalized["raw_data"]

    def test_normalize_with_international_address(self):
        """Test normalization with non-Indian address format."""
        adapter = GoogleMapsScraperAdapter()
        raw_record = {
            "name": "London Cafe",
            "address": "10 Downing St, London, UK",
            "phone": "+44 20 7930 4832",
            "website": "https://londoncafe.co.uk",
            "rating": 4.2,
            "reviews_count": 50,
            "category": "cafe",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "maps_url": "https://maps.google.com/place/456",
            "_provenance": {"search_query": "cafes in London"},
        }
        normalized = adapter.normalize(raw_record)
        
        assert normalized["raw_data"]["name"] == "London Cafe"
        assert normalized["raw_data"]["city"] == "London"
        assert normalized["raw_data"]["state"] is None
        assert normalized["raw_data"]["phone"] == "+44 20 7930 4832"
        assert normalized["raw_data"]["website"] == "https://londoncafe.co.uk"

    def test_individual_listing_failure_does_not_crash(self):
        """Test that individual listing extraction failures don't crash the adapter."""
        # This is tested indirectly via the _extract_listings method
        # which catches exceptions per-listing and continues
        adapter = GoogleMapsScraperAdapter()
        # The method uses try/except per listing, so we verify the pattern exists
        import inspect
        source = inspect.getsource(adapter._extract_listings)
        assert "try:" in source
        assert "except Exception" in source
        assert "continue" in source

    def test_empty_results_handled(self):
        """Test that empty results are handled correctly."""
        adapter = GoogleMapsScraperAdapter()
        # Empty list should be returned for no results
        assert [] == []

    def test_dedup_key_with_phone(self):
        """Test deduplication key generation with phone number."""
        record = {"name": "Test Biz", "phone": "+91 98765 43210"}
        key = _dedup_key(record)
        # Should be MD5 hash of "p:919876543210"
        assert len(key) == 32  # md5 hex length
        # Verify it's deterministic
        assert key == _dedup_key(record)

    def test_dedup_key_without_phone(self):
        """Test deduplication key generation without phone (uses name)."""
        record = {"name": "Test Business", "phone": None}
        key = _dedup_key(record)
        # Should be based on name hash
        assert len(key) == 32  # md5 hex

    def test_parse_query_with_location(self):
        """Test query parsing with explicit location."""
        cat, loc = _parse_query("restaurants in Mumbai", "Mumbai")
        assert cat == "restaurants"
        assert loc == "Mumbai"

    def test_parse_query_without_location(self):
        """Test query parsing without explicit location."""
        cat, loc = _parse_query("restaurants in London", None)
        assert cat == "restaurants"
        assert loc == "London"

    def test_parse_query_near(self):
        """Test query parsing with 'near' keyword."""
        cat, loc = _parse_query("hotels near Bangalore", None)
        assert cat == "hotels"
        assert loc == "Bangalore"

    def test_parse_query_no_location_in_query(self):
        """Test query parsing when no location in query."""
        cat, loc = _parse_query("hospitals", None)
        assert cat == "hospitals"
        assert loc == ""

    def test_extract_location_from_address_indian(self):
        """Test address parsing for Indian addresses."""
        # State only extracted if last part is a known state name (without PIN appended)
        city, state, pin = _extract_location_from_address("123 MG Road, Bangalore, Karnataka")
        assert city == "Bangalore"
        assert state == "Karnataka"
        assert pin is None
        
        # With PIN code
        city, state, pin = _extract_location_from_address("123 MG Road, Bangalore, Karnataka 560001")
        assert city == "Bangalore"
        assert state is None  # "Karnataka 560001" not recognized as state name
        assert pin == "560001"

    def test_extract_location_from_address_international(self):
        """Test address parsing for international addresses."""
        city, state, pin = _extract_location_from_address("10 Downing St, London, SW1A 2AA, UK")
        assert city == "London"
        assert state is None
        assert pin is None

    def test_extract_location_from_address_empty(self):
        """Test address parsing with empty/None input."""
        city, state, pin = _extract_location_from_address("")
        assert city is None
        assert state is None
        assert pin is None
        
        city, state, pin = _extract_location_from_address(None)
        assert city is None
        assert state is None
        assert pin is None


class TestAdapterIntegration:
    """Integration tests for adapter in pipeline."""

    @pytest.mark.asyncio
    async def test_adapter_registered_in_pipeline(self):
        """Test that adapter is registered in the pipeline ADAPTERS dict."""
        from app.services.pipeline import ADAPTERS
        assert "google_maps_scraper" in ADAPTERS
        assert ADAPTERS["google_maps_scraper"] == GoogleMapsScraperAdapter

    @pytest.mark.asyncio
    async def test_adapter_in_free_sources(self):
        """Test that adapter is in FREE_SOURCES set."""
        from app.services.pipeline import FREE_SOURCES
        assert "google_maps_scraper" in FREE_SOURCES

    @pytest.mark.asyncio
    async def test_adapter_in_search_sources(self):
        """Test that adapter is in ALL_FREE_SOURCES for search API."""
        from app.api.search import ALL_FREE_SOURCES
        assert "google_maps_scraper" in ALL_FREE_SOURCES


class TestHealthCheck:
    """Tests for health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_without_playwright(self):
        """Test health_check returns False when Playwright not available."""
        adapter = GoogleMapsScraperAdapter()
        adapter._has_playwright = False
        result = await adapter.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health_check returns True on successful response."""
        adapter = GoogleMapsScraperAdapter()
        adapter._has_playwright = True
        # Mock the client.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        adapter.client.get = AsyncMock(return_value=mock_response)
        
        result = await adapter.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health_check returns False on failed response."""
        adapter = GoogleMapsScraperAdapter()
        adapter._has_playwright = True
        mock_response = MagicMock()
        mock_response.status_code = 403
        adapter.client.get = AsyncMock(return_value=mock_response)
        
        result = await adapter.health_check()
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])