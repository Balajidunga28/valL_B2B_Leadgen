"""
url: /backend/app/api/auth.py
About:
  Authentication API endpoints for ValLG. Handles user signup, login with
  JWT token generation, current user retrieval, and logout.
"""

import re
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, SignupRequest, UserResponse
from app.services.auth import authenticate_user, create_access_token, hash_password
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT token."""
    user = await authenticate_user(db, request.email, request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token(user.id, user.organization_id)

    return LoginResponse(
        token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            organization_id=str(user.organization_id),
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        organization_id=str(current_user.organization_id),
    )


@router.post("/logout")
async def logout():
    """Logout endpoint. Client clears token locally."""
    return {"detail": "Logged out"}


@router.post("/signup", response_model=LoginResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user with a new organization."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create organization
    org_id = uuid4()
    slug = re.sub(r"[^a-z0-9]+", "-", request.name.lower().strip())[:80].strip("-")
    if not slug:
        slug = f"org-{org_id.hex[:8]}"
    org = Organization(
        id=org_id,
        name=request.name,
        slug=slug,
        plan="free",
    )
    db.add(org)

    # Create user
    user = User(
        id=uuid4(),
        organization_id=org_id,
        email=request.email,
        password_hash=hash_password(request.password),
        name=request.name,
        role="admin",
        is_active=True,
    )
    db.add(user)

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.organization_id)

    return LoginResponse(
        token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            organization_id=str(user.organization_id),
        ),
    )
