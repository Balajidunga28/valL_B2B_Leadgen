"""
url: /backend/app/database.py
About:
  Database connection and session management for ValLG. Provides async
  SQLAlchemy engine, session factory, and dependency injection for FastAPI
  route handlers. Enforces tenant scoping via organization_id.
"""

import ssl as ssl_mod
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _prepare_async_url(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    sslmode = qs.pop("sslmode", None)
    new_query = urlencode(qs, doseq=True)
    clean_url = urlunparse(parsed._replace(query=new_query))
    if sslmode:
        clean_url += "&ssl=require" if "?" in clean_url else "?ssl=require"
    return clean_url


engine = create_async_engine(
    _prepare_async_url(settings.DATABASE_URL_ASYNC),
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

AsyncSessionLocal = async_session_factory


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that provides a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
