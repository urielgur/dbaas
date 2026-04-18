from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.local_provider import hash_password
from app.auth.provider import AuthProvider
from app.auth.tokens import create_access_token
from app.dependencies import get_auth_provider, get_current_user, get_user_storage
from app.models.user import (
    CreateUserRequest,
    LoginRequest,
    TokenResponse,
    UserRecord,
    UserResponse,
)
from app.storage.user_storage import UserJsonStorage

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    provider: Annotated[AuthProvider, Depends(get_auth_provider)],
) -> TokenResponse:
    user = await provider.authenticate(body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.username)
    return TokenResponse(access_token=token)


@router.get("/auth/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse(
        username=current_user.username,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    current_user: Annotated[UserRecord, Depends(get_current_user)],
    user_storage: Annotated[UserJsonStorage, Depends(get_user_storage)],
) -> UserResponse:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    existing = await user_storage.get_user(body.username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User '{body.username}' already exists",
        )
    record = UserRecord(
        username=body.username,
        hashed_password=hash_password(body.password),
        is_admin=body.is_admin,
    )
    await user_storage.create_user(record)
    return UserResponse(
        username=record.username,
        is_admin=record.is_admin,
        created_at=record.created_at,
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: Annotated[UserRecord, Depends(get_current_user)],
    user_storage: Annotated[UserJsonStorage, Depends(get_user_storage)],
) -> list[UserResponse]:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    users = await user_storage.list_users()
    return [
        UserResponse(username=u.username, is_admin=u.is_admin, created_at=u.created_at)
        for u in users
    ]
