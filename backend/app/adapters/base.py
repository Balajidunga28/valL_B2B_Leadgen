"""
url: /backend/app/adapters/base.py
About:
  Abstract base class for all source adapters. Defines the common interface
  that all adapters must implement: search, normalize, and health check.
  This ensures consistent behavior across all data sources.
"""

from abc import ABC, abstractmethod
from typing import Any

import httpx


class SourceAdapter(ABC):
    """Base class for all data source adapters."""

    name: str = "base"
    display_name: str = "Base Source"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    @abstractmethod
    async def search(
        self,
        query: str,
        location: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Search the source for matching records.

        Args:
            query: Search query (e.g., "IT companies in Bangalore")
            location: Optional location filter
            limit: Max results to return
            offset: Pagination offset

        Returns:
            List of raw records in source-native format.
        """
        ...

    @abstractmethod
    def normalize(self, raw_record: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize a raw record to the common RawRecord schema.

        Args:
            raw_record: Source-native format record

        Returns:
            Normalized record matching RawRecord schema fields.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the source is available and API key is valid.

        Returns:
            True if healthy, False otherwise.
        """
        ...
