from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.collectors.argocd_collector import ArgoCDCollector
from app.collectors.gitlab_collector import GitLabCollector
from app.config import settings
from app.scanner.scan_orchestrator import ScanOrchestrator, ScanScheduler
from app.storage.base import StorageBackend
from app.storage.json_storage import JsonStorageBackend
from app.storage.mongo_storage import MongoStorageBackend


def get_storage() -> StorageBackend:
    if settings.storage.backend == "mongodb":
        if not settings.storage.mongo_uri:
            raise RuntimeError("STORAGE_MONGO_URI must be set when STORAGE_BACKEND=mongodb")
        return MongoStorageBackend(settings.storage.mongo_uri, settings.storage.mongo_database)
    return JsonStorageBackend(settings.storage.json_path)


def get_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=30.0)


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
