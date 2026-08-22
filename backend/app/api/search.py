"""
url: /backend/app/api/search.py
About:
  Search API endpoints for ValLG. Handles search queries, creates pipeline
  runs, orchestrates source adapters. Extraction runs inline, post-processing
  (clean → validate → enrich → score) runs as a background task so the
  response returns within Render's 30s HTTP timeout.
  All endpoints require JWT authentication.
"""

import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session_factory
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.search import SearchRequest, SearchResponse, PipelineRunResponse, RawRecordResponse, VALID_SOURCES
from app.services.pipeline import run_extraction, get_pipeline_run, get_raw_records

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])

# Backward compatibility - tests expect this
ALL_FREE_SOURCES = list(VALID_SOURCES)


@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute a search query against selected data sources.
    Runs the full pipeline (clean → validate → enrich → score) so results are
    immediately available on the Results page.
    """
    sources = request.sources
    
    # Validate sources are valid (schema does this, but double-check)
    invalid = [s for s in sources if s not in VALID_SOURCES]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source(s): {', '.join(invalid)}",
        )
    
    # Enforce reasonable limit
    if request.limit < 1 or request.limit > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 200",
        )

    try:
        pipeline_run = await run_extraction(
            db=db,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            query=request.query,
            location=request.location,
            sources=sources,
            limit=request.limit,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Save pipeline_run fields before pipeline chain (commits expire ORM objects)
    run_id = pipeline_run.id
    run_query_text = pipeline_run.query_text
    run_status = pipeline_run.status
    run_sources_used = pipeline_run.sources_used or []
    run_total_extracted = pipeline_run.total_extracted
    run_error_message = pipeline_run.error_message
    run_created_at = pipeline_run.created_at
    org_id = current_user.organization_id

    # Run post-processing (clean → validate → enrich → score) in background
    # so the response returns within Render's 30s HTTP timeout
    async def _run_post_processing():
        from app.services.level3 import run_clean
        from app.services.level4 import run_validate
        from app.services.level5 import run_enrich
        from app.services.level6 import run_score
        async with async_session_factory() as bg_db:
            try:
                await run_clean(bg_db, org_id, pipeline_run_id=run_id)
                await run_validate(bg_db, org_id)
                await run_enrich(bg_db, org_id)
                await run_score(bg_db, org_id)
                await bg_db.commit()
            except Exception as e:
                logger.warning("Background post-processing error: %s", e)
                await bg_db.rollback()

    asyncio.create_task(_run_post_processing())

    return SearchResponse(
        pipeline_run=PipelineRunResponse(
            id=str(run_id),
            query_text=run_query_text,
            status=run_status,
            sources_used=run_sources_used,
            total_extracted=run_total_extracted,
            error_message=run_error_message,
            created_at=run_created_at,
        ),
        records=[],
        total_count=run_total_extracted,
    )


@router.get("/runs/{run_id}", response_model=PipelineRunResponse)
async def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific pipeline run by ID."""
    from uuid import UUID

    try:
        run_uuid = UUID(run_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid run ID format",
        )

    run = await get_pipeline_run(db, run_uuid, current_user.organization_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline run not found",
        )

    return PipelineRunResponse(
        id=str(run.id),
        query_text=run.query_text,
        status=run.status,
        sources_used=run.sources_used or [],
        total_extracted=run.total_extracted,
        created_at=run.created_at,
    )
