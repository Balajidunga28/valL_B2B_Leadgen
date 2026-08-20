"""
url: /backend/tests/test_search_regression.py
About:
  Regression tests for the ValLG search pipeline.
  Verifies that the search architecture is fully query-driven:
  - No hardcoded keyword allowlist gates searches
  - Any category from user query is accepted
  - No default city/state injection
  - Worldwide multi-source fallback
  - Relevance filtering is permissive (rejects only clearly irrelevant)
"""

import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.geo import (
    check_category_relevance,
    get_category_synonyms,
    get_coords_for_city,
)
from app.adapters.openstreetmap import OpenStreetMapAdapter
from app.services.pipeline import (
    _extract_location_from_query,
    _extract_category_from_query,
    _validate_location,
)


# ── All 12 required test queries ──────────────────────────────────
QUERIES = [
    ("hospitals in Rajahmundry", "hospitals", "Rajahmundry"),
    ("restaurants in London", "restaurants", "London"),
    ("parks in Chennai", "parks", "Chennai"),
    ("medical stores in Eluru", "medical stores", "Eluru"),
    ("pharmacies in Hyderabad", "pharmacies", "Hyderabad"),
    ("OYO hotels in Vijayawada", "OYO hotels", "Vijayawada"),
    ("petrol pumps in Bangalore", "petrol pumps", "Bangalore"),
    ("wedding halls in Hyderabad", "wedding halls", "Hyderabad"),
    ("solar companies in Germany", "solar companies", "Germany"),
    ("coworking spaces in Singapore", "coworking spaces", "Singapore"),
    ("startups in Kolkata", "startups", "Kolkata"),
    ("clothing shops in Hyderabad", "clothing shops", "Hyderabad"),
]


class TestQueryParsing:
    """Test that ALL 12 queries parse category and location correctly."""

    def test_no_default_city_injected(self):
        """Verify no default Eluru/Andhra Pradesh is injected for non-Indian queries."""
        for query, expected_cat, expected_loc in QUERIES:
            loc = _extract_location_from_query(query)
            cat = _extract_category_from_query(query)
            assert cat == expected_cat, f"Query '{query}': expected cat='{expected_cat}', got '{cat}'"
            assert loc == expected_loc, f"Query '{query}': expected loc='{expected_loc}', got '{loc}'"

    def test_all_12_queries_parse(self):
        """All 12 required queries must parse correctly."""
        for query, expected_cat, expected_loc in QUERIES:
            loc = _extract_location_from_query(query)
            cat = _extract_category_from_query(query)
            assert cat is not None and len(cat) > 0, f"Query '{query}': category is empty"
            assert loc is not None and len(loc) > 0, f"Query '{query}': location is empty"

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

    def test_no_location_query(self):
        loc = _extract_location_from_query("restaurants")
        cat = _extract_category_from_query("restaurants")
        assert loc is None
        assert cat == "restaurants"


class TestNoKeywordAllowlist:
    """Verify that NO predefined keyword list gates what can be searched.
    
    The user's query determines the search — not a hardcoded category map.
    """

    def test_arbitrary_categories_accepted(self):
        """ALL categories from the 12 queries must be accepted by relevance check."""
        # Records that contain at least one domain-specific word from the category should pass
        test_cases = [
            # (category, record_name, record_industry, expected)
            ("hospitals", "City Hospital", "healthcare", True),
            ("restaurants", "Pizza Palace Restaurant", "food", True),
            ("parks", "Green Valley Park", "recreation", True),
            ("medical stores", "Health Plus Medical Store", "pharmacy", True),
            ("pharmacies", "MedPlus Pharmacy", "pharmaceutical", True),
            ("OYO hotels", "OYO Townhouse", "hospitality", True),
            ("petrol pumps", "HP Petrol Pump", "fuel", True),
            ("wedding halls", "Grand Wedding Hall", "events", True),
            ("solar companies", "SunPower Solar Solutions", "energy", True),
            ("coworking spaces", "WeWork Coworking", "office", True),
            ("startups", "TechVenture Startup", "technology", True),
            ("clothing shops", "Fashion World Clothing", "retail", True),
            # Categories NOT in any predefined list — must still work
            ("architects", "Best Architects Studio", "architecture", True),
            ("tutoring centers", "Math Guru Tutoring Center", "education", True),
            ("interior designers", "Luxe Interior Designers", "design", True),
            ("photographers", "SnapShot Photographer", "photography", True),
            ("plumbers", "Quick Fix Plumbers", "services", True),
            ("dog walkers", "Happy Paws Dog Walking", "pets", True),
        ]
        for category, name, industry, expected in test_cases:
            record = {"raw_data": {"name": name, "industry": industry, "address": "123 Main St"}}
            result = check_category_relevance(record, category)
            assert result == expected, f"Category '{category}' with record '{name}': expected {expected}, got {result}"

    def test_irrelevant_records_rejected(self):
        """Clearly unrelated records should be rejected when they have no meaningful content."""
        # Record with no contact info and no word overlap — should be rejected
        record = {"raw_data": {"name": "Random Article", "industry": "blog", "address": None, "phone": None, "website": None}}
        result = check_category_relevance(record, "hospitals")
        # This should be rejected because: no word overlap, no contact info
        assert result is False, f"Expected irrelevant record to be rejected, got {result}"

    def test_record_with_contact_info_rejected_if_no_category_match(self):
        """Records with contact info but no category word overlap are rejected.
        
        The old behavior accepted any record with a phone/address regardless of
        category. This caused contamination: sweet shops appearing in clothing
        searches because they have phone numbers. Now, records must match at
        least one domain-specific category word.
        """
        record = {"raw_data": {"name": "Best Business Corp", "phone": "+1234567890", "address": "456 Commerce St"}}
        result = check_category_relevance(record, "hospitals")
        assert result is False, f"Expected unrelated record to be rejected, got {result}"

    def test_empty_record_passes(self):
        """Empty records should pass (fail-open)."""
        record = {"raw_data": {}}
        assert check_category_relevance(record, "hospitals") is True
        assert check_category_relevance(record, "parks") is True
        assert check_category_relevance(record, "solar companies") is True

    def test_empty_category_passes(self):
        """No category should pass (fail-open)."""
        record = {"raw_data": {"name": "Anything"}}
        assert check_category_relevance(record, "") is True

    def test_no_predefined_keyword_groups_used(self):
        """Verify that CATEGORY_KEYWORD_GROUPS is NOT the gating mechanism.
        
        Categories not in CATEGORY_KEYWORD_GROUPS must still work.
        """
        # These categories are NOT in CATEGORY_KEYWORD_GROUPS
        novel_categories = [
            "architects", "tutoring", "interior designers", "photographers",
            "plumbers", "dog walkers", "wedding planners", "solar panel installers",
            "EV charging stations", "co-working spaces", "cloud kitchens",
        ]
        for cat in novel_categories:
            record = {"raw_data": {"name": f"Best {cat} Inc", "address": "123 Main St"}}
            result = check_category_relevance(record, cat)
            assert result is True, f"Novel category '{cat}' was rejected — keyword allowlist is still gating"


class TestCategoryRelevance:
    """Test that relevance validation is permissive but filters junk."""

    def test_word_overlap_accepted(self):
        """Record containing any category word is accepted."""
        record = {"raw_data": {"name": "Sunny Pharmacy", "industry": "health", "address": "123 Medical Rd"}}
        assert check_category_relevance(record, "medical stores") is True

    def test_no_overlap_with_contact_rejected(self):
        """Record with no word overlap AND contact info is rejected when category has domain words."""
        record = {"raw_data": {"name": "Best Business Corp", "phone": "+1234567890", "address": "456 St"}}
        assert check_category_relevance(record, "hospitals") is False

    def test_no_overlap_no_contact_rejected(self):
        """Record with no word overlap AND no contact info is rejected (likely junk)."""
        record = {"raw_data": {"name": "Random Blog Post", "industry": "blog"}}
        assert check_category_relevance(record, "hospitals") is False

    def test_clothing_matches_fashion(self):
        """'clothing shops' should match a record containing 'clothing'."""
        record = {"raw_data": {"name": "Trendy Clothing Store", "industry": "retail"}}
        assert check_category_relevance(record, "clothing shops") is True

    def test_parks_matches_park(self):
        """'parks' should match a record containing 'park'."""
        record = {"raw_data": {"name": "Green Valley Park", "industry": "recreation"}}
        assert check_category_relevance(record, "parks") is True

    def test_solar_matches_solar(self):
        """'solar companies' should match a record containing 'solar'."""
        record = {"raw_data": {"name": "SunPower Solar Solutions", "industry": "energy"}}
        assert check_category_relevance(record, "solar companies") is True


class TestOSMTags:
    """Test that OSM tag generation uses query text directly."""

    def test_known_category_gets_tags(self):
        """Known categories get structured OSM tags."""
        adapter = OpenStreetMapAdapter.__new__(OpenStreetMapAdapter)
        tags = adapter._build_tags("restaurants in London")
        # Should have amenity=restaurant tag
        tag_keys = [k for k, v in tags]
        assert "amenity" in tag_keys or "name" in tag_keys

    def test_unknown_category_gets_name_search(self):
        """Unknown categories ALWAYS get a name-based search."""
        adapter = OpenStreetMapAdapter.__new__(OpenStreetMapAdapter)
        tags = adapter._build_tags("wedding halls in Hyderabad")
        # Must have a name tag
        tag_keys = [k for k, v in tags]
        assert "name" in tag_keys, f"Unknown category must get name search, got: {tags}"

    def test_novel_category_never_returns_empty(self):
        """Arbitrary categories must never produce empty tag list."""
        adapter = OpenStreetMapAdapter.__new__(OpenStreetMapAdapter)
        novel_queries = [
            "coworking spaces in Singapore",
            "solar companies in Germany",
            "wedding halls in Hyderabad",
            "petrol pumps in Bangalore",
            "OYO hotels in Vijayawada",
            "photographers in Mumbai",
            "interior designers in Delhi",
        ]
        for query in novel_queries:
            tags = adapter._build_tags(query)
            assert len(tags) > 0, f"Query '{query}' produced empty tags"
            assert "name" in [k for k, v in tags], f"Query '{query}' missing name search tag"


class TestLocationValidation:
    """Test that location validation works for worldwide queries."""

    def test_london_restaurant_passes(self):
        record = {"raw_data": {"name": "Pizza Express", "city": "London", "address": "123 London St"}}
        assert _validate_location(record, "London", None) is True

    def test_wrong_city_rejected(self):
        record = {"raw_data": {"name": "Pizza Place", "city": "Seattle", "address": "456 Pike St"}}
        assert _validate_location(record, "London", None) is False

    def test_no_location_data_passes(self):
        record = {"raw_data": {"name": "Business Name", "phone": "+442071234567"}}
        assert _validate_location(record, "London", None) is True

    def test_noise_record_rejected(self):
        record = {"raw_data": {"name": "Food", "phone": None, "address": None, "city": None}}
        assert _validate_location(record, "London", None) is False

    def test_coord_based_match(self):
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

    def test_get_category_synonyms_no_group_lookup(self):
        """Synonyms must NOT use predefined keyword groups."""
        # Novel category must return at least the raw category
        result = get_category_synonyms("wedding planners")
        assert "wedding planners" in result
        # Must not be restricted to a small predefined list
        assert len(result) >= 1

    def test_synonyms_singular_plural(self):
        """Should generate singular/plural variations."""
        result = get_category_synonyms("hospitals")
        assert "hospitals" in result
        assert "hospital" in result


class TestScoring:
    """Test that scoring doesn't penalize for unknown enrichment data."""

    def test_unknown_industry_not_zero(self):
        from app.services.score import score_industry
        # None industry should give 0.5, not 0.0
        assert score_industry(None) == 0.5

    def test_known_industry_full_score(self):
        from app.services.score import score_industry
        assert score_industry("healthcare") == 1.0

    def test_unknown_size_not_zero(self):
        from app.services.score import score_size
        assert score_size(None) == 0.5

    def test_unknown_tech_not_zero(self):
        from app.services.score import score_technology
        assert score_technology(None) == 0.5

    def test_spa_not_zero_score(self):
        """A spa record should not get 0 total score."""
        from app.services.score import compute_total_score, score_industry, score_size, score_location, score_technology, score_data_quality, score_validation
        total = compute_total_score(
            industry_score=score_industry(None),
            size_score=score_size(None),
            location_score=score_location("Delhi", 28.61, 77.21, "123 Spa Road"),
            technology_score=score_technology(None),
            data_quality_score=score_data_quality("+911234567890", None, None, "123 Spa Road", None, None, 4.5, 100),
            validation_score=score_validation("VALID"),
        )
        assert total > 0, f"Expected positive score for spa record, got {total}"


class TestLocationFuzzy:
    """Test that fuzzy city matching works."""

    def test_new_delhi_matches_delhi(self):
        record = {"raw_data": {"name": "Spa Delhi", "city": "New Delhi", "address": "123 Main St"}}
        assert _validate_location(record, "Delhi", None) is True

    def test_south_delhi_matches_delhi(self):
        record = {"raw_data": {"name": "Spa Delhi", "city": "South Delhi", "address": "123 Main St"}}
        assert _validate_location(record, "Delhi", None) is True

    def test_name_only_record_accepted(self):
        """Record with only a name should be accepted (real business)."""
        record = {"raw_data": {"name": "Best Spa Delhi"}}
        assert _validate_location(record, "Delhi", None) is True

    def test_completely_empty_rejected(self):
        """Record with absolutely no data should be rejected."""
        record = {"raw_data": {}}
        assert _validate_location(record, "Delhi", None) is False


class TestCategoryContamination:
    """Regression tests: category contamination must be rejected.
    
    When searching for a specific category, unrelated businesses must NOT
    appear in results just because they share generic words like "shop",
    "store", or have contact information.
    """

    def test_clothing_shops_rejects_sweet_shops(self):
        """Sweet shops must NOT appear in 'clothing shops' results."""
        sweet_shop = {
            "raw_data": {
                "name": "Sri Venkateswara Sweets & Namkeen",
                "industry": "food",
                "address": "MG Road, Hyderabad",
                "phone": "+919876543210",
                "city": "Hyderabad",
            }
        }
        assert check_category_relevance(sweet_shop, "clothing shops") is False

    def test_clothing_shops_rejects_bakeries(self):
        """Bakeries must NOT appear in 'clothing shops' results."""
        bakery = {
            "raw_data": {
                "name": "Cake Palace Bakery",
                "industry": "food",
                "address": "Banjara Hills, Hyderabad",
                "phone": "+919876543211",
                "city": "Hyderabad",
            }
        }
        assert check_category_relevance(bakery, "clothing shops") is False

    def test_clothing_shops_rejects_hospitals(self):
        """Hospitals must NOT appear in 'clothing shops' results."""
        hospital = {
            "raw_data": {
                "name": "Apollo Hospital",
                "industry": "healthcare",
                "address": "Jubilee Hills, Hyderabad",
                "phone": "+919876543212",
                "city": "Hyderabad",
            }
        }
        assert check_category_relevance(hospital, "clothing shops") is False

    def test_clothing_shops_rejects_hotels(self):
        """Hotels must NOT appear in 'clothing shops' results."""
        hotel = {
            "raw_data": {
                "name": "Taj Hotel Hyderabad",
                "industry": "hospitality",
                "address": "Tank Bund, Hyderabad",
                "phone": "+919876543213",
                "city": "Hyderabad",
            }
        }
        assert check_category_relevance(hotel, "clothing shops") is False

    def test_clothing_shops_accepts_actual_clothing(self):
        """Actual clothing businesses MUST appear in 'clothing shops' results."""
        clothing_cases = [
            {"raw_data": {"name": "Fashion World Clothing", "industry": "retail", "address": "Hyderabad"}},
            {"raw_data": {"name": "Trendy Wear Shop", "industry": "clothing", "address": "Hyderabad"}},
            {"raw_data": {"name": "Men's Clothing Outlet", "industry": "fashion", "address": "Hyderabad"}},
            {"raw_data": {"name": "Clothing Paradise", "industry": "retail", "address": "Hyderabad"}},
            {"raw_data": {"name": "Textile Gallery", "industry": "clothing", "address": "Hyderabad"}},
        ]
        for rec in clothing_cases:
            result = check_category_relevance(rec, "clothing shops")
            assert result is True, f"Clothing record '{rec['raw_data']['name']}' was rejected"

    def test_hotels_rejects_restaurants(self):
        """Restaurants must NOT appear in 'hotels' results."""
        restaurant = {
            "raw_data": {
                "name": "Biryani House",
                "industry": "food",
                "address": "Hyderabad",
                "phone": "+919876543214",
            }
        }
        assert check_category_relevance(restaurant, "hotels") is False

    def test_hotels_accepts_actual_hotels(self):
        """Actual hotels MUST appear in 'hotels' results."""
        hotel = {
            "raw_data": {
                "name": "Grand Hotel Hyderabad",
                "industry": "hospitality",
                "address": "Hyderabad",
            }
        }
        assert check_category_relevance(hotel, "hotels") is True

    def test_pharmacies_rejects_clothing(self):
        """Clothing stores must NOT appear in 'pharmacies' results."""
        clothing = {
            "raw_data": {
                "name": "Fashion Hub",
                "industry": "retail",
                "address": "Hyderabad",
                "phone": "+919876543215",
            }
        }
        assert check_category_relevance(clothing, "pharmacies") is False

    def test_pharmacies_accepts_actual_pharmacies(self):
        """Actual pharmacies MUST appear in 'pharmacies' results."""
        pharmacy = {
            "raw_data": {
                "name": "MedPlus Pharmacy",
                "industry": "pharmaceutical",
                "address": "Hyderabad",
            }
        }
        assert check_category_relevance(pharmacy, "pharmacies") is True

    def test_generic_category_accepts_broadly(self):
        """Purely generic categories (e.g., 'shops') should accept broadly."""
        any_business = {
            "raw_data": {
                "name": "Any Business Shop",
                "industry": "retail",
                "address": "Hyderabad",
                "phone": "+919876543216",
            }
        }
        assert check_category_relevance(any_business, "shops") is True
        assert check_category_relevance(any_business, "stores") is True
        assert check_category_relevance(any_business, "companies") is True

    def test_empty_record_always_passes(self):
        """Empty records always pass (fail-open)."""
        empty = {"raw_data": {}}
        assert check_category_relevance(empty, "clothing shops") is True
        assert check_category_relevance(empty, "hospitals") is True

    def test_record_without_name_or_industry_passes(self):
        """Records with no name/industry pass (can't judge relevance)."""
        minimal = {"raw_data": {"phone": "+919876543217", "address": "Hyderabad"}}
        assert check_category_relevance(minimal, "clothing shops") is True

    def test_spa_rejects_unrelated(self):
        """Unrelated businesses must NOT appear in 'spa' results."""
        unrelated = {
            "raw_data": {
                "name": "Computer Repair Shop",
                "industry": "technology",
                "address": "Delhi",
                "phone": "+919876543218",
            }
        }
        assert check_category_relevance(unrelated, "spa") is False

    def test_spa_accepts_actual_spa(self):
        """Actual spas MUST appear in 'spa' results."""
        spa = {
            "raw_data": {
                "name": "Bliss Wellness Spa",
                "industry": "wellness",
                "address": "Delhi",
            }
        }
        assert check_category_relevance(spa, "spa") is True

    def test_solar_companies_rejects_food(self):
        """Food businesses must NOT appear in 'solar companies' results."""
        food = {
            "raw_data": {
                "name": "Domino's Pizza",
                "industry": "food",
                "address": "Delhi",
                "phone": "+919876543219",
            }
        }
        assert check_category_relevance(food, "solar companies") is False

    def test_solar_companies_accepts_actual_solar(self):
        """Actual solar businesses MUST appear in 'solar companies' results."""
        solar = {
            "raw_data": {
                "name": "SunPower Solar Solutions",
                "industry": "energy",
                "address": "Delhi",
            }
        }
        assert check_category_relevance(solar, "solar companies") is True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
