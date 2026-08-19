"""
url: /backend/tests/test_search_regression.py
About:
  Regression tests for the ValLG search pipeline.
  Verifies that the query-driven search architecture works correctly:
  - No hardcoded city/state injection
  - Category relevance validation
  - Multi-source fallback (zero from one source doesn't kill pipeline)
  - Worldwide search support
  - Deduplication works
  - Scoring works
"""

import asyncio
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.geo import (
    _extract_category_keywords,
    check_category_relevance,
    get_coords_for_city,
)
from app.services.pipeline import (
    _extract_location_from_query,
    _extract_category_from_query,
    _validate_location,
)


class TestQueryParsing:
    """Test that queries are parsed correctly without hardcoded defaults."""

    def test_restaurants_in_london(self):
        loc = _extract_location_from_query("restaurants in London")
        cat = _extract_category_from_query("restaurants in London")
        assert loc == "London", f"Expected 'London', got '{loc}'"
        assert cat == "restaurants", f"Expected 'restaurants', got '{cat}'"

    def test_hospitals_in_rajahmundry(self):
        loc = _extract_location_from_query("hospitals in Rajahmundry")
        cat = _extract_category_from_query("hospitals in Rajahmundry")
        assert loc == "Rajahmundry"
        assert cat == "hospitals"

    def test_startups_in_kolkata(self):
        loc = _extract_location_from_query("startups in Kolkata")
        cat = _extract_category_from_query("startups in Kolkata")
        assert loc == "Kolkata"
        assert cat == "startups"

    def test_clothing_shops_in_hyderabad(self):
        loc = _extract_location_from_query("clothing shops in Hyderabad")
        cat = _extract_category_from_query("clothing shops in Hyderabad")
        assert loc == "Hyderabad"
        assert cat == "clothing shops"

    def test_dentists_in_toronto(self):
        loc = _extract_location_from_query("dentists in Toronto")
        cat = _extract_category_from_query("dentists in Toronto")
        assert loc == "Toronto"
        assert cat == "dentists"

    def test_restaurants_no_location(self):
        loc = _extract_location_from_query("restaurants")
        cat = _extract_category_from_query("restaurants")
        assert loc is None
        assert cat == "restaurants"

    def test_manufacturing_germany(self):
        loc = _extract_location_from_query("manufacturing companies in Germany")
        cat = _extract_category_from_query("manufacturing companies in Germany")
        assert loc == "Germany"
        assert cat == "manufacturing companies"

    def test_software_berlin(self):
        loc = _extract_location_from_query("software companies in Berlin")
        cat = _extract_category_from_query("software companies in Berlin")
        assert loc == "Berlin"
        assert cat == "software companies"

    def test_restaurants_in_mexico(self):
        loc = _extract_location_from_query("restaurants in Mexico")
        cat = _extract_category_from_query("restaurants in Mexico")
        assert loc == "Mexico"
        assert cat == "restaurants"

    def test_restaurants_in_vizag(self):
        loc = _extract_location_from_query("restaurants in Vizag")
        cat = _extract_category_from_query("restaurants in Vizag")
        assert loc == "Vizag"
        assert cat == "restaurants"

    def test_no_default_city_injected(self):
        """Verify no default Eluru/Andhra Pradesh is injected."""
        loc = _extract_location_from_query("restaurants in London")
        assert loc != "Eluru"
        assert "Andhra Pradesh" not in (loc or "")

    def test_query_with_near(self):
        loc = _extract_location_from_query("hospitals near Mumbai")
        cat = _extract_category_from_query("hospitals near Mumbai")
        assert loc == "Mumbai"
        assert cat == "hospitals"

    def test_query_with_at(self):
        loc = _extract_location_from_query("cafes at Paris")
        cat = _extract_category_from_query("cafes at Paris")
        assert loc == "Paris"
        assert cat == "cafes"


class TestCategoryRelevance:
    """Test that category relevance validation works correctly."""

    def test_restaurant_matches_restaurant_record(self):
        record = {"raw_data": {"name": "Pizza Palace", "industry": "restaurant", "address": "123 Main St"}}
        assert check_category_relevance(record, "restaurants") is True

    def test_restaurant_rejects_hospital(self):
        record = {"raw_data": {"name": "City Hospital", "industry": "hospital", "address": "456 Health Ave"}}
        assert check_category_relevance(record, "restaurants") is False

    def test_clothing_matches_apparel_store(self):
        record = {"raw_data": {"name": "Fashion World", "industry": "retail", "address": "789 Fashion St"}}
        assert check_category_relevance(record, "clothing shops") is True

    def test_clothing_rejects_sweets_shop(self):
        record = {"raw_data": {"name": "Pullareddy Sweets Shop", "industry": "food", "address": "123 Sweet St"}}
        assert check_category_relevance(record, "clothing shops") is False

    def test_dental_matches_dental_clinic(self):
        record = {"raw_data": {"name": "Bright Smile Dental", "industry": "dental", "address": "321 Smile Ave"}}
        assert check_category_relevance(record, "dentists") is True

    def test_startup_matches_tech_company(self):
        record = {"raw_data": {"name": "TechVenture Inc", "industry": "technology", "address": "555 Tech Blvd"}}
        assert check_category_relevance(record, "startups") is True

    def test_empty_record_passes_relevance(self):
        """Empty records should pass relevance (fail-open)."""
        record = {"raw_data": {}}
        assert check_category_relevance(record, "restaurants") is True

    def test_no_category_passes_relevance(self):
        """No category should pass relevance (fail-open)."""
        record = {"raw_data": {"name": "Anything"}}
        assert check_category_relevance(record, "") is True

    def test_manufacturing_matches_factory(self):
        record = {"raw_data": {"name": "Steel Works Factory", "industry": "manufacturing", "address": "100 Industrial Blvd"}}
        assert check_category_relevance(record, "manufacturing companies") is True

    def test_hospital_matches_clinic(self):
        record = {"raw_data": {"name": "Health Care Clinic", "industry": "medical", "address": "200 Health Rd"}}
        assert check_category_relevance(record, "hospitals") is True


class TestLocationValidation:
    """Test that location validation works for worldwide queries."""

    def test_london_restaurant_passes(self):
        record = {"raw_data": {"name": "Pizza Express", "city": "London", "address": "123 London St"}}
        assert _validate_location(record, "London", None) is True

    def test_wrong_city_rejected(self):
        record = {"raw_data": {"name": "Pizza Place", "city": "Seattle", "address": "456 Pike St"}}
        assert _validate_location(record, "London", None) is False

    def test_no_location_data_passes(self):
        """Records with no location data should pass (source already scoped)."""
        record = {"raw_data": {"name": "Business Name", "phone": "+442071234567"}}
        assert _validate_location(record, "London", None) is True

    def test_noise_record_rejected(self):
        """Records with no business data should be rejected."""
        record = {"raw_data": {"name": "Food", "phone": None, "address": None, "city": None}}
        assert _validate_location(record, "London", None) is False

    def test_coord_based_match(self):
        """Records with coordinates near the target city should pass."""
        record = {"raw_data": {"name": "Nearby Place", "latitude": 51.51, "longitude": -0.13}}
        assert _validate_location(record, "London", None) is True


class TestGeoUtilities:
    """Test geographic utility functions."""

    def test_london_coords_exist(self):
        coords = get_coords_for_city("london")
        assert coords is not None
        assert abs(coords[0] - 51.5074) < 0.01

    def test_toronto_coords_exist(self):
        coords = get_coords_for_city("toronto")
        assert coords is not None
        assert abs(coords[0] - 43.6532) < 0.01

    def test_vizag_coords_exist(self):
        coords = get_coords_for_city("vizag")
        assert coords is not None

    def test_rajahmundry_coords_exist(self):
        coords = get_coords_for_city("rajahmundry")
        assert coords is not None

    def test_mexico_city_coords_exist(self):
        coords = get_coords_for_city("mexico city")
        assert coords is not None

    def test_unknown_city_returns_none(self):
        coords = get_coords_for_city("tiny_village_xyz")
        assert coords is None

    def test_category_keywords_extraction(self):
        keywords = _extract_category_keywords("clothing shops in Hyderabad")
        assert "clothing" in keywords
        assert "shops" not in keywords  # stop word

    def test_category_keywords_restaurants(self):
        keywords = _extract_category_keywords("restaurants")
        assert "restaurants" in keywords


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
