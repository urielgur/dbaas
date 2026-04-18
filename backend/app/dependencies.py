from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.auth.local_provider import LocalAuthProvider
from app.auth.provider import AuthProvider
from app.auth.tokens import decode_access_token
from app.collectors.argocd_collector import ArgoCDCollector
from app.collectors.gitlab_collector import GitLabCollector
from app.config import settings
from app.models.user import UserRecord
from app.scanner.scan_orchestrator import ScanOrchestrator, ScanScheduler
from app.storage.base import StorageBackend
from app.storage.user_storage import UserJsonStorage

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_storage(request: Request) -> StorageBackend:
    return request.app.state.storage


def get_user_storage() -> UserJsonStorage:
    return UserJsonStorage(settings.auth.users_json_path)


def get_auth_provider(
    user_storage: Annotated[UserJsonStorage, Depends(get_user_storage)],
) -> AuthProvider:
    # To switch to Active Directory: return ActiveDirectoryAuthProvider(settings.ad)
    return LocalAuthProvider(user_storage)


async def get_current_user(
    token: Annotated[str, Depends(_oauth2_scheme)],
    user_storage: Annotated[UserJsonStorage, Depends(get_user_storage)],
) -> UserRecord:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exc
    user = await user_storage.get_user(token_data.sub)
    if user is None:
        raise credentials_exc
    return user


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_gitlab_collector(
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> GitLabCollector:
    return GitLabCollector(settings.gitlab, client)


def get_argocd_collector(
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> ArgoCDCollector:
    return ArgoCDCollector(settings.argocd.instances, client)


def get_orchestrator(request: Request) -> ScanOrchestrator:
    return request.app.state.orchestrator


def get_scheduler(request: Request) -> ScanScheduler:
    return request.app.state.scheduler
