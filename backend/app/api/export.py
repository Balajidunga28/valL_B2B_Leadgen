"""
url: /backend/app/api/export.py
About:
  Export API endpoints for ValLG. Generates CSV exports of raw records
  for a pipeline run or filtered query. Returns CSV as downloadable file.
  All endpoints require JWT authentication.
"""

import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.results import list_raw_records

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/csv")
async def export_csv(
    pipeline_run_id: str | None = Query(None, description="Filter by pipeline run ID"),
    source_adapter: str | None = Query(None, description="Filter by source adapter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export raw records as CSV file.
    Downloads a CSV with columns: name, address, phone, website, rating, source, etc.
    """
    run_uuid = None
    if pipeline_run_id:
        try:
            run_uuid = UUID(pipeline_run_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pipeline_run_id format",
            )

    # Fetch all matching records (no pagination for export)
    records, total_count = await list_raw_records(
        db=db,
        organization_id=current_user.organization_id,
        pipeline_run_id=run_uuid,
        source_adapter=source_adapter,
        page=1,
        page_size=10000,  # Max export size
    )

    if total_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No records to export",
        )

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Name",
        "Address",
        "City",
        "State",
        "Country",
        "Phone",
        "International Phone",
        "Website",
        "Rating",
        "Review Count",
        "Business Status",
        "Latitude",
        "Longitude",
        "Google Maps URL",
        "Place ID",
        "Source",
        "Retrieved At",
    ])

    # Data rows
    for record in records:
        raw = record.raw_data or {}
        writer.writerow([
            raw.get("name", ""),
            raw.get("address", ""),
            raw.get("city", ""),
            raw.get("state", ""),
            raw.get("country", ""),
            raw.get("phone", ""),
            raw.get("phone_intl", ""),
            raw.get("website", ""),
            raw.get("rating", ""),
            raw.get("review_count", ""),
            raw.get("business_status", ""),
            raw.get("latitude", ""),
            raw.get("longitude", ""),
            raw.get("google_maps_url", ""),
            record.source_record_id or "",
            record.source_adapter,
            record.retrieved_at.isoformat() if record.retrieved_at else "",
        ])

    # Prepare download
    output.seek(0)
    filename = f"vallg_export_{current_user.organization_id}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
