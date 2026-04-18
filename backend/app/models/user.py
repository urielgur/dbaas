from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class UserRecord(BaseModel):
    username: str
    hashed_password: str
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserResponse(BaseModel):
    username: str
    is_admin: bool
    created_at: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CreateUserRequest(BaseModel):
    username: str
    password: str
    is_admin: bool = False
