"""
url: /backend/app/main.py
About:
  FastAPI application entry point for ValLG. Configures CORS, includes
  API routers, seeds default data, and provides health check endpoint.
  Application startup creates database tables for development convenience.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.api.auth import router as auth_router
from app.api.search import router as search_router
from app.api.results import router as results_router
from app.api.dashboard import router as dashboard_router
from app.api.settings import router as settings_router
from app.api.export import router as export_router
from app.api.sources import router as sources_router
from app.api.level3 import router as level3_router
from app.api.level4 import router as level4_router
from app.api.level5 import router as level5_router
from app.api.level6 import router as level6_router
from app.api.level7 import router as level7_router
from app.api.leads import router as leads_router
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables and seed data on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_database()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(results_router)
app.include_router(dashboard_router)
app.include_router(settings_router)
app.include_router(export_router)
app.include_router(sources_router)
app.include_router(level3_router)
app.include_router(level4_router)
app.include_router(level5_router)
app.include_router(level6_router)
app.include_router(level7_router)
app.include_router(leads_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "ok", "version": settings.APP_VERSION}
