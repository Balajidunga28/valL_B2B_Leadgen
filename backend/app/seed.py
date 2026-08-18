"""
url: /backend/app/seed.py
About:
  Seed data for initial development. Creates a default organization and admin
  user so the application can be used immediately after database setup.
  Only runs if no users exist in the database.
"""

import asyncio
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.services.auth import hash_password


async def seed_database():
    """Seed database with default organization and admin user."""
    async with AsyncSessionLocal() as db:
        # Check if users already exist
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            return  # Database already seeded

        # Create default organization
        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="Default Organization",
            slug="default",
            plan="free",
        )
        db.add(org)

        # Create admin user
        user = User(
            id=uuid4(),
            organization_id=org_id,
            email="admin@vallg.com",
            password_hash=hash_password("admin123"),
            name="Admin",
            role="admin",
            is_active=True,
        )
        db.add(user)

        await db.commit()
        print(f"Seeded database with org={org.id}, user=admin@vallg.com")
