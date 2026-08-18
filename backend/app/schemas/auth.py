"""
url: /backend/app/schemas/auth.py
About:
  Pydantic schemas for authentication API. Defines request/response shapes
  for login, token, and current user endpoints.
"""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: str
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    organization_id: str

    model_config = {"from_attributes": True}
