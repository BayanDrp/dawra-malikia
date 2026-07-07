from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class MessageResponse(BaseModel):
    message: str


class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    display_name: str
    is_active: bool
    is_verified: bool
    email_notifications: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = None
    email_notifications: bool | None = None


class ChangePassword(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class ForgotPassword(BaseModel):
    email: str = Field(..., max_length=255)


class ResetPassword(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshToken(BaseModel):
    refresh_token: str


class LoginLogResponse(BaseModel):
    id: int
    ip_address: str | None
    user_agent: str | None
    timestamp: datetime
    successful: bool

    model_config = {"from_attributes": True}


class LoginEventEmail(BaseModel):
    email: str
    ip_address: str | None
    user_agent: str | None
    timestamp: datetime


class CourseRegistrationCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    email: str = Field(..., max_length=255)
    phone: str = Field(..., min_length=7, max_length=20)
    gender: str = Field(..., pattern=r"^(ذكر|أنثى|male|female)$")
    city: str = Field(..., min_length=2, max_length=100)
    notes: str = ""


class CourseRegistrationResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    gender: str
    city: str
    status: str
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateStatus(BaseModel):
    status: str = Field(..., pattern=r"^(pending|approved|rejected)$")


class AdminReply(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)


class BulkAction(BaseModel):
    ids: list[int] = Field(..., min_length=1)
    action: str = Field(..., pattern=r"^(approve|reject|delete)$")
