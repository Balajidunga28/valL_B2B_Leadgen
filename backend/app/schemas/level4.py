"""
url: /backend/app/schemas/level4.py
About:
  Pydantic schemas for Level 4 VALIDATE API.
"""

from datetime import datetime
from pydantic import BaseModel


class ValidateResponse(BaseModel):
    companies_read: int
    validated: int
    valid: int
    invalid: int
    unknown: int
    email_valid: int
    email_invalid: int
    email_not_available: int
    phone_valid: int
    phone_invalid: int
    phone_not_available: int
    website_valid: int
    website_invalid: int
    website_not_available: int
    business_valid: int
    business_invalid: int
    business_unknown: int


class CompanyValidationResponse(BaseModel):
    company_id: str
    company_name: str
    email_status: str
    phone_status: str
    website_status: str
    business_existence_status: str
    overall_status: str
    validation_results: dict | None = None
    validated_at: datetime | None = None

    model_config = {"from_attributes": True}
