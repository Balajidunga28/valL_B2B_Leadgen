"""
url: /backend/app/api/level3.py
About:
  Level 3 CLEAN API endpoint. Triggers the cleaning pipeline that reads
  raw_records from Level 2, applies standardization, performs entity
  resolution, and creates Company records as the cleaned representation.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.level3 import CleanRequest, CleanResponse
from app.services.level3 import run_clean

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/level3", tags=["level3"])


@router.post("/clean", response_model=CleanResponse)
async def clean(
    request: CleanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute Level 3 CLEAN pipeline.

    Reads raw_records from Level 2, applies cleaning/standardization,
    performs entity resolution to identify duplicates, and creates
    Company records as the cleaned representation.

    Raw records are NOT deleted or modified (except normalized_data and
    company_id fields are populated).

    Can be re-run safely — previous Company records for the organization
    are cleared and re-created.
    """
    pipeline_run_id = None
    if request.pipeline_run_id:
        try:
            pipeline_run_id = UUID(request.pipeline_run_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pipeline_run_id format",
            )

    try:
        result = await run_clean(
            db=db,
            organization_id=current_user.organization_id,
            pipeline_run_id=pipeline_run_id,
        )
    except Exception as e:
        logger.error("Level 3 clean failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleaning pipeline failed: {str(e)}",
        )

    return CleanResponse(**result)
