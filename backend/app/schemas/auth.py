from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid
from datetime import datetime


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    phone: Optional[str] = None
    state: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    state: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
