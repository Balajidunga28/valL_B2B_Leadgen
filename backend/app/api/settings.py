"""
url: /backend/app/api/settings.py
About:
  Settings API endpoints for ValLG. Manages API keys for data sources.
  Keys are stored with a hint (last 4 chars) for display purposes.
  All endpoints require JWT authentication.
"""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.source_api_key import SourceApiKey
from app.api.deps import get_current_user
from app.schemas.settings import (
    ApiKeyCreateRequest,
    ApiKeyResponse,
    ApiKeyListResponse,
    ApiKeyDeleteResponse,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/api-keys", response_model=ApiKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the current organization."""
    result = await db.execute(
        select(SourceApiKey).where(
            SourceApiKey.organization_id == current_user.organization_id,
        )
    )
    keys = list(result.scalars().all())

    return ApiKeyListResponse(
        keys=[
            ApiKeyResponse(
                id=str(key.id),
                source_adapter=key.source_adapter,
                api_key_hint=key.api_key_hint,
                status=key.status,
                last_verified_at=key.last_verified_at,
                quota_used=key.quota_used,
                quota_limit=key.quota_limit,
                created_at=key.created_at,
            )
            for key in keys
        ]
    )


@router.post("/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add or update an API key for a source adapter."""
    # Check if key already exists for this source
    result = await db.execute(
        select(SourceApiKey).where(
            SourceApiKey.organization_id == current_user.organization_id,
            SourceApiKey.source_adapter == request.source_adapter,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing key
        existing.api_key_encrypted = request.api_key
        existing.api_key_hint = f"****{request.api_key[-4:]}" if len(request.api_key) >= 4 else "****"
        existing.status = "active"
        await db.commit()
        await db.refresh(existing)
        key = existing
    else:
        # Create new key
        key = SourceApiKey(
            id=uuid4(),
            organization_id=current_user.organization_id,
            source_adapter=request.source_adapter,
            api_key_encrypted=request.api_key,
            api_key_hint=f"****{request.api_key[-4:]}" if len(request.api_key) >= 4 else "****",
            status="active",
            quota_used=0,
        )
        db.add(key)
        await db.commit()
        await db.refresh(key)

    return ApiKeyResponse(
        id=str(key.id),
        source_adapter=key.source_adapter,
        api_key_hint=key.api_key_hint,
        status=key.status,
        last_verified_at=key.last_verified_at,
        quota_used=key.quota_used,
        quota_limit=key.quota_limit,
        created_at=key.created_at,
    )


@router.delete("/api-keys/{key_id}", response_model=ApiKeyDeleteResponse)
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an API key."""
    from uuid import UUID

    try:
        key_uuid = UUID(key_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid key ID format",
        )

    result = await db.execute(
        select(SourceApiKey).where(
            SourceApiKey.id == key_uuid,
            SourceApiKey.organization_id == current_user.organization_id,
        )
    )
    key = result.scalar_one_or_none()

    if key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    await db.delete(key)
    await db.commit()

    return ApiKeyDeleteResponse(
        success=True,
        message=f"API key for {key.source_adapter} deleted",
    )
