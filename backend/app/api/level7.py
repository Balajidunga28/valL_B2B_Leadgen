"""
url: /backend/app/api/level7.py
About:
  Level 7 EXPORT API endpoint. Returns scored/filtered leads as a
  downloadable CSV file. Supports the same filtering parameters as
  Level 6 leads endpoint. Read-only — no data modification.
"""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.level7 import export_leads_csv

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/level7", tags=["level7"])


@router.get("/export/csv")
async def export_csv(
    min_score: float | None = Query(None, description="Minimum total score"),
    max_score: float | None = Query(None, description="Maximum total score"),
    industry: str | None = Query(None, description="Industry filter"),
    has_phone: bool | None = Query(None, description="Has phone number"),
    has_email: bool | None = Query(None, description="Has email"),
    has_website: bool | None = Query(None, description="Has website"),
    validation_status: str | None = Query(None, description="Validation status"),
    city: str | None = Query(None, description="City filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export scored leads as a downloadable CSV file.

    Supports the same filtering parameters as Level 6 GET /leads.
    Export is read-only — no records are modified or deleted.
    """
    csv_string, record_count, audit = await export_leads_csv(
        db=db,
        organization_id=current_user.organization_id,
        min_score=min_score,
        max_score=max_score,
        industry=industry,
        has_phone=has_phone,
        has_email=has_email,
        has_website=has_website,
        validation_status=validation_status,
        city=city,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"vallg_leads_{timestamp}.csv"

    # Build content-disposition with audit metadata in custom header
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Export-Record-Count": str(record_count),
        "X-Export-Audit": json.dumps(audit),
    }

    return StreamingResponse(
        iter([csv_string.encode("utf-8")]),
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )
