"""
url: /backend/app/api/results.py
About:
  Results API endpoints for ValLG. Provides read-only access to raw records
  and pipeline runs with filtering, pagination, and organization scoping.
  All endpoints require JWT authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.results import (
    RawRecordDetailResponse,
    RawRecordListResponse,
    PipelineRunDetailResponse,
    PipelineRunListResponse,
)
from app.services.results import (
    list_raw_records,
    get_raw_record,
    list_pipeline_runs,
)

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/records", response_model=RawRecordListResponse)
async def get_records(
    pipeline_run_id: str | None = Query(None, description="Filter by pipeline run ID"),
    source_adapter: str | None = Query(None, description="Filter by source adapter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Results per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List raw records with optional filtering and pagination."""
    run_uuid = None
    if pipeline_run_id:
        try:
            run_uuid = UUID(pipeline_run_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pipeline_run_id format",
            )

    records, total_count = await list_raw_records(
        db=db,
        organization_id=current_user.organization_id,
        pipeline_run_id=run_uuid,
        source_adapter=source_adapter,
        page=page,
        page_size=page_size,
    )

    return RawRecordListResponse(
        records=[
            RawRecordDetailResponse(
                id=str(record.id),
                source_adapter=record.source_adapter,
                source_record_id=record.source_record_id,
                raw_data=record.raw_data or {},
                normalized_data=record.normalized_data,
                status=record.status,
                error_message=record.error_message,
                retrieved_at=record.retrieved_at,
                created_at=record.created_at,
            )
            for record in records
        ],
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.get("/records/{record_id}", response_model=RawRecordDetailResponse)
async def get_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single raw record by ID."""
    try:
        record_uuid = UUID(record_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid record ID format",
        )

    record = await get_raw_record(db, record_uuid, current_user.organization_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )

    return RawRecordDetailResponse(
        id=str(record.id),
        source_adapter=record.source_adapter,
        source_record_id=record.source_record_id,
        raw_data=record.raw_data or {},
        normalized_data=record.normalized_data,
        status=record.status,
        error_message=record.error_message,
        retrieved_at=record.retrieved_at,
        created_at=record.created_at,
    )


@router.get("/runs", response_model=PipelineRunListResponse)
async def get_runs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List pipeline runs for the current organization."""
    runs, total_count = await list_pipeline_runs(
        db=db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
    )

    return PipelineRunListResponse(
        runs=[
            PipelineRunDetailResponse(
                id=str(run.id),
                query_text=run.query_text,
                query_params=run.query_params or {},
                status=run.status,
                sources_used=run.sources_used or [],
                total_extracted=run.total_extracted,
                total_cleaned=run.total_cleaned,
                total_deduplicated=run.total_deduplicated,
                total_valid=run.total_valid,
                total_enriched=run.total_enriched,
                error_message=run.error_message,
                started_at=run.started_at,
                completed_at=run.completed_at,
                created_at=run.created_at,
            )
            for run in runs
        ],
        total_count=total_count,
    )


@router.get("/runs/{run_id}", response_model=PipelineRunDetailResponse)
async def get_run_detail(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific pipeline run by ID."""
    from app.services.pipeline import get_pipeline_run

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

    return PipelineRunDetailResponse(
        id=str(run.id),
        query_text=run.query_text,
        query_params=run.query_params or {},
        status=run.status,
        sources_used=run.sources_used or [],
        total_extracted=run.total_extracted,
        total_cleaned=run.total_cleaned,
        total_deduplicated=run.total_deduplicated,
        total_valid=run.total_valid,
        total_enriched=run.total_enriched,
        error_message=run.error_message,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )
