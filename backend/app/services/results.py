"""
url: /backend/app/services/results.py
About:
  Results service for ValLG. Provides read-only access to raw records
  and pipeline runs with filtering, pagination, and organization scoping.
"""

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline_run import PipelineRun
from app.models.raw_record import RawRecord


async def list_raw_records(
    db: AsyncSession,
    organization_id: UUID,
    pipeline_run_id: UUID | None = None,
    source_adapter: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[RawRecord], int]:
    """
    List raw records with optional filtering and pagination.

    Returns:
        Tuple of (records, total_count)
    """
    query = select(RawRecord).where(RawRecord.organization_id == organization_id)

    if pipeline_run_id:
        query = query.where(RawRecord.pipeline_run_id == pipeline_run_id)
    if source_adapter:
        query = query.where(RawRecord.source_adapter == source_adapter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(RawRecord.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    records = list(result.scalars().all())

    return records, total_count


async def get_raw_record(
    db: AsyncSession,
    record_id: UUID,
    organization_id: UUID,
) -> RawRecord | None:
    """Fetch a single raw record by ID."""
    result = await db.execute(
        select(RawRecord).where(
            RawRecord.id == record_id,
            RawRecord.organization_id == organization_id,
        )
    )
    return result.scalar_one_or_none()


async def list_pipeline_runs(
    db: AsyncSession,
    organization_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[PipelineRun], int]:
    """
    List pipeline runs for an organization.

    Returns:
        Tuple of (runs, total_count)
    """
    query = select(PipelineRun).where(
        PipelineRun.organization_id == organization_id
    )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(PipelineRun.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    runs = list(result.scalars().all())

    return runs, total_count
