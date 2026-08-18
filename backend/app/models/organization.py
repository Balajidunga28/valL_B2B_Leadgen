"""
url: /backend/app/models/organization.py
About:
  Organization entity representing a tenant in ValLG. Every tenant-owned
  record links back to an organization. Organization ownership is derived
  server-side from the authenticated user — never from client requests.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Organization(BaseModel):
    """Multi-tenant organization. All data is scoped to an organization."""
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")

    # Relationships
    users = relationship("User", back_populates="organization", lazy="selectin")
    companies = relationship("Company", back_populates="organization", lazy="selectin")
    pipeline_runs = relationship("PipelineRun", back_populates="organization", lazy="selectin")
