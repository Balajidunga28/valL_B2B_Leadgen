"""
url: /backend/app/adapters/__init__.py
About:
  Source adapter package for ValLG. Contains adapter implementations for
  each approved external data source. Adapters implement a common interface
  and are registered in the adapter registry.
"""

from app.adapters.base import SourceAdapter
from app.adapters.google_places import GooglePlacesAdapter

__all__ = ["SourceAdapter", "GooglePlacesAdapter"]
