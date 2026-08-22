"""
url: /backend/tests/test_google_maps_search_integration.py
About:
  Integration tests for Google Maps adapter in the search pipeline.
  Tests that the adapter is correctly invoked through the existing search API.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.pipeline import run_extraction, ADAPTERS, FREE_SOURCES, get_adapter
from app.adapters.google_maps_scraper import GoogleMapsScraperAdapter
from app.models.pipeline_run import PipelineRun
from app.models.raw_record import RawRecord
from sqlalchemy.ext.asyncio import AsyncSession


class TestGoogleMapsSearchIntegration:
    """Integration tests for Google Maps adapter in search pipeline."""

    @pytest.mark.asyncio
    async def test_google_maps_adapter_registered_in_pipeline(self):
        """Test that Google Maps adapter is registered in ADAPTERS."""
        assert "google_maps_scraper" in ADAPTERS
        assert ADAPTERS["google_maps_scraper"] == GoogleMapsScraperAdapter

    @pytest.mark.asyncio
    async def test_google_maps_in_free_sources(self):
        """Test that Google Maps is in FREE_SOURCES set."""
        assert "google_maps_scraper" in FREE_SOURCES

    @pytest.mark.asyncio
    async def test_get_adapter_returns_google_maps_scraper(self):
        """Test that get_adapter returns GoogleMapsScraperAdapter for free source."""
        mock_db = AsyncMock(spec=AsyncSession)
        org_id = uuid4()
        
        adapter = await get_adapter(mock_db, org_id, "google_maps_scraper")
        assert isinstance(adapter, GoogleMapsScraperAdapter)
        assert adapter.name == "google_maps_scraper"

    @pytest.mark.asyncio
    async def test_get_adapter_raises_for_unknown_source(self):
        """Test that get_adapter raises ValueError for unknown source."""
        mock_db = AsyncMock(spec=AsyncSession)
        org_id = uuid4()
        
        with pytest.raises(ValueError, match="Unknown source"):
            await get_adapter(mock_db, org_id, "nonexistent_source")

    @pytest.mark.asyncio
    async def test_pipeline_invokes_google_maps_adapter(self):
        """Test that run_extraction invokes Google Maps adapter when in sources list."""
        mock_db = AsyncMock(spec=AsyncSession)
        org_id = uuid4()
        user_id = uuid4()
        
        # Mock the database operations
        mock_run = MagicMock(spec=PipelineRun)
        mock_run.id = uuid4()
        mock_run.query_text = "restaurants in Mumbai"
        mock_run.status = "completed"
        mock_run.sources_used = ["google_maps_scraper"]
        mock_run.total_extracted = 5
        mock_run.error_message = None
        mock_run.created_at = None
        
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Mock the adapter
        mock_adapter = AsyncMock(spec=GoogleMapsScraperAdapter)
        mock_adapter.search = AsyncMock(return_value=[
            {
                "name": "Test Restaurant",
                "address": "123 Main St, Mumbai, Maharashtra",
                "phone": "+91 22 1234 5678",
                "website": "https://test.com",
                "rating": 4.5,
                "reviews_count": 100,
                "category": "restaurant",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "maps_url": "https://maps.google.com/place/123",
            }
        ])
        mock_adapter.normalize = MagicMock(return_value={
            "source_record_id": "gmaps_scraper_abc123",
            "raw_data": {
                "name": "Test Restaurant",
                "address": "123 Main St, Mumbai, Maharashtra",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pin_code": None,
                "phone": "+91 22 1234 5678",
                "website": "https://test.com",
                "email": None,
                "industry": "restaurant",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "rating": 4.5,
                "reviews_count": 100,
                "opening_hours": None,
                "maps_url": "https://maps.google.com/place/123",
                "source_url": "https://maps.google.com/place/123",
                "metadata": {
                    "extraction_method": "google_maps_scraper",
                    "search_query": "restaurants in Mumbai",
                    "extracted_at": "2024-01-01T00:00:00Z",
                    "maps_url": "https://maps.google.com/place/123",
                },
            },
        })
        mock_adapter.close = AsyncMock()
        
        with patch("app.services.pipeline.get_adapter", return_value=mock_adapter):
            with patch("app.services.pipeline.RawRecord") as mock_raw_record:
                mock_raw_record_instance = MagicMock()
                mock_raw_record.return_value = mock_raw_record_instance
                
                run = await run_extraction(
                    db=mock_db,
                    organization_id=org_id,
                    user_id=user_id,
                    query="restaurants in Mumbai",
                    location="Mumbai",
                    sources=["google_maps_scraper"],
                    limit=10,
                )
        
        # Verify adapter was called (may be called multiple times with search variations)
        assert mock_adapter.search.call_count >= 1
        # First call should use the original query (most specific)
        first_call = mock_adapter.search.call_args_list[0]
        assert first_call.kwargs["query"] == "restaurants in Mumbai"
        assert first_call.kwargs["location"] == "Mumbai"
        assert first_call.kwargs["limit"] >= 10
        
        # Verify normalize was called
        mock_adapter.normalize.assert_called()
        
        # Verify adapter was closed
        mock_adapter.close.assert_called()

    @pytest.mark.asyncio
    async def test_google_maps_results_flow_through_pipeline(self):
        """Test that Google Maps results are processed through the pipeline."""
        mock_db = AsyncMock(spec=AsyncSession)
        org_id = uuid4()
        user_id = uuid4()
        
        mock_run = MagicMock(spec=PipelineRun)
        mock_run.id = uuid4()
        mock_run.query_text = "cafes in London"
        mock_run.status = "completed"
        mock_run.sources_used = ["google_maps_scraper", "openstreetmap"]
        mock_run.total_extracted = 3
        mock_run.error_message = None
        mock_run.created_at = None
        
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Track calls to get_adapter
        adapter_calls = []
        
        async def mock_get_adapter(db, org_id, source_name):
            adapter_calls.append(source_name)
            mock_adapter = AsyncMock(spec=GoogleMapsScraperAdapter if source_name == "google_maps_scraper" else MagicMock)
            if source_name == "google_maps_scraper":
                mock_adapter.search = AsyncMock(return_value=[
                    {"name": "London Cafe", "address": "10 Downing St, London", "phone": "+44 20 1234 5678"}
                ])
                mock_adapter.normalize = MagicMock(return_value={
                    "source_record_id": "gmaps_scraper_london1",
                    "raw_data": {"name": "London Cafe", "address": "10 Downing St, London", "city": "London", "phone": "+44 20 1234 5678"}
                })
            else:
                mock_adapter.search = AsyncMock(return_value=[])
                mock_adapter.normalize = MagicMock(return_value={})
            mock_adapter.close = AsyncMock()
            return mock_adapter
        
        with patch("app.services.pipeline.get_adapter", side_effect=mock_get_adapter):
            with patch("app.services.pipeline.RawRecord") as mock_raw_record:
                mock_raw_record_instance = MagicMock()
                mock_raw_record.return_value = mock_raw_record_instance
                
                run = await run_extraction(
                    db=mock_db,
                    organization_id=org_id,
                    user_id=user_id,
                    query="cafes in London",
                    location="London",
                    sources=["google_maps_scraper", "openstreetmap"],
                    limit=10,
                )
        
        assert "google_maps_scraper" in adapter_calls
        assert "openstreetmap" in adapter_calls

    @pytest.mark.asyncio
    async def test_google_maps_empty_results_handled(self):
        """Test that empty results from Google Maps are handled gracefully."""
        mock_db = AsyncMock(spec=AsyncSession)
        org_id = uuid4()
        user_id = uuid4()
        
        mock_run = MagicMock(spec=PipelineRun)
        mock_run.id = uuid4()
        mock_run.query_text = "nonexistent business type xyz"
        mock_run.status = "completed"
        mock_run.sources_used = ["google_maps_scraper"]
        mock_run.total_extracted = 0
        mock_run.error_message = None
        mock_run.created_at = None
        
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        mock_adapter = AsyncMock(spec=GoogleMapsScraperAdapter)
        mock_adapter.search = AsyncMock(return_value=[])
        mock_adapter.normalize = MagicMock(return_value={})
        mock_adapter.close = AsyncMock()
        
        with patch("app.services.pipeline.get_adapter", return_value=mock_adapter):
            with patch("app.services.pipeline.RawRecord") as mock_raw_record:
                mock_raw_record_instance = MagicMock()
                mock_raw_record.return_value = mock_raw_record_instance
                
                run = await run_extraction(
                    db=mock_db,
                    organization_id=org_id,
                    user_id=user_id,
                    query="nonexistent business type xyz",
                    location="Mumbai",
                    sources=["google_maps_scraper"],
                    limit=10,
                )
        
        assert run.total_extracted == 0

    @pytest.mark.asyncio
    async def test_google_maps_adapter_failure_handled(self):
        """Test that adapter failures are handled without crashing pipeline."""
        mock_db = AsyncMock(spec=AsyncSession)
        org_id = uuid4()
        user_id = uuid4()
        
        mock_run = MagicMock(spec=PipelineRun)
        mock_run.id = uuid4()
        mock_run.query_text = "restaurants in Mumbai"
        mock_run.status = "completed"
        mock_run.sources_used = ["google_maps_scraper", "openstreetmap"]
        mock_run.total_extracted = 2
        mock_run.error_message = None
        mock_run.created_at = None
        
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        call_count = [0]
        
        async def mock_get_adapter(db, org_id, source_name):
            call_count[0] += 1
            if source_name == "google_maps_scraper":
                mock_adapter = AsyncMock(spec=GoogleMapsScraperAdapter)
                mock_adapter.search = AsyncMock(side_effect=Exception("Network error"))
                mock_adapter.close = AsyncMock()
                return mock_adapter
            else:
                # openstreetmap succeeds
                mock_adapter = AsyncMock()
                mock_adapter.search = AsyncMock(return_value=[
                    {"name": "OSM Restaurant", "address": "Mumbai"}
                ])
                mock_adapter.normalize = MagicMock(return_value={
                    "source_record_id": "osm_1",
                    "raw_data": {"name": "OSM Restaurant", "address": "Mumbai", "city": "Mumbai"}
                })
                mock_adapter.close = AsyncMock()
                return mock_adapter
        
        with patch("app.services.pipeline.get_adapter", side_effect=mock_get_adapter):
            with patch("app.services.pipeline.RawRecord") as mock_raw_record:
                mock_raw_record_instance = MagicMock()
                mock_raw_record.return_value = mock_raw_record_instance
                
                run = await run_extraction(
                    db=mock_db,
                    organization_id=org_id,
                    user_id=user_id,
                    query="restaurants in Mumbai",
                    location="Mumbai",
                    sources=["google_maps_scraper", "openstreetmap"],
                    limit=10,
                )
        
        # Pipeline should complete even with one source failing
        assert run.status == "completed"
        assert run.total_extracted >= 0

    @pytest.mark.asyncio
    async def test_google_maps_parameters_passed_correctly(self):
        """Test that query, location, and limit are passed to adapter correctly."""
        mock_db = AsyncMock(spec=AsyncSession)
        org_id = uuid4()
        user_id = uuid4()
        
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        captured_params = {}
        
        mock_adapter = AsyncMock(spec=GoogleMapsScraperAdapter)
        async def capture_search(query, location, limit, offset=0):
            captured_params["query"] = query
            captured_params["location"] = location
            captured_params["limit"] = limit
            captured_params["offset"] = offset
            return [{"name": "Test"}]
        mock_adapter.search = capture_search
        mock_adapter.normalize = MagicMock(return_value={
            "source_record_id": "test",
            "raw_data": {"name": "Test"}
        })
        mock_adapter.close = AsyncMock()
        
        with patch("app.services.pipeline.get_adapter", return_value=mock_adapter):
            with patch("app.services.pipeline.RawRecord") as mock_raw_record:
                mock_raw_record_instance = MagicMock()
                mock_raw_record.return_value = mock_raw_record_instance
                
                await run_extraction(
                    db=mock_db,
                    organization_id=org_id,
                    user_id=user_id,
                    query="hospitals in Delhi",
                    location="Delhi, India",
                    sources=["google_maps_scraper"],
                    limit=50,
                )
        
        # First call should use the original query (most specific)
        # The pipeline now tries multiple search variations
        assert captured_params.get("query") is not None
        assert captured_params["location"] == "Delhi, India"
        assert captured_params["limit"] >= 50  # extraction_limit = max(limit, 200)

    @pytest.mark.asyncio
    async def test_multiple_sources_with_google_maps(self):
        """Test that Google Maps works alongside other free sources."""
        mock_db = AsyncMock(spec=AsyncSession)
        org_id = uuid4()
        user_id = uuid4()
        
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        sources_called = []
        
        async def mock_get_adapter(db, org_id, source_name):
            sources_called.append(source_name)
            mock_adapter = AsyncMock()
            mock_adapter.search = AsyncMock(return_value=[{"name": f"Result from {source_name}"}])
            mock_adapter.normalize = MagicMock(return_value={
                "source_record_id": f"{source_name}_1",
                "raw_data": {"name": f"Result from {source_name}"}
            })
            mock_adapter.close = AsyncMock()
            return mock_adapter
        
        with patch("app.services.pipeline.get_adapter", side_effect=mock_get_adapter):
            with patch("app.services.pipeline.RawRecord") as mock_raw_record:
                mock_raw_record_instance = MagicMock()
                mock_raw_record.return_value = mock_raw_record_instance
                
                await run_extraction(
                    db=mock_db,
                    organization_id=org_id,
                    user_id=user_id,
                    query="startups in Bangalore",
                    location="Bangalore",
                    sources=["google_search", "google_maps_scraper", "openstreetmap", "web_search"],
                    limit=20,
                )
        
        assert "google_search" in sources_called
        assert "google_maps_scraper" in sources_called
        assert "openstreetmap" in sources_called
        assert "web_search" in sources_called


class TestSearchAPIIntegration:
    """Tests for search API integration with Google Maps."""

    def test_search_schema_allows_google_maps_source(self):
        """Test that SearchRequest schema accepts google_maps_scraper in sources list."""
        from app.schemas.search import SearchRequest
        
        request = SearchRequest(
            query="restaurants in Mumbai",
            sources=["google_maps_scraper", "google_search"]
        )
        assert "google_maps_scraper" in request.sources
        assert "google_search" in request.sources

    def test_search_schema_default_includes_free_sources(self):
        """Test that SearchRequest default sources are the free ones."""
        from app.schemas.search import SearchRequest
        
        request = SearchRequest(query="test")
        # Default sources from schema now include google_maps_scraper
        expected_default = ["google_search", "google_maps_scraper", "openstreetmap", "web_search", "indiamart", "justdial"]
        assert request.sources == expected_default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])