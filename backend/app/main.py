from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Trigger DB type registration before anything else runs
import app.registry.types  # noqa: F401
from app.api import auth, connect, databases, scan
from app.auth.local_provider import hash_password
from app.collectors.argocd_collector import ArgoCDCollector
from app.collectors.gitlab_collector import GitLabCollector
from app.config import settings
from app.models.user import UserRecord
from app.scanner.scan_orchestrator import ScanOrchestrator, ScanScheduler
from app.storage.base import StorageBackend
from app.storage.json_storage import JsonStorageBackend
from app.storage.mongo_storage import MongoStorageBackend
from app.storage.user_storage import UserJsonStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Fail fast on missing secret key before anything starts
    if not settings.auth.secret_key:
        raise RuntimeError(
            "AUTH_SECRET_KEY is not set. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # Shared HTTP client — one connection pool for all collectors
    http_client = httpx.AsyncClient(timeout=30.0)

    # Storage singleton — one instance (and one lock) shared across all requests
    storage: StorageBackend
    if settings.storage.backend == "mongodb":
        if not settings.storage.mongo_uri:
            raise RuntimeError("STORAGE_MONGO_URI must be set when STORAGE_BACKEND=mongodb")
        storage = MongoStorageBackend(settings.storage.mongo_uri, settings.storage.mongo_database)
    else:
        storage = JsonStorageBackend(settings.storage.json_path)

    gitlab_collector = GitLabCollector(settings.gitlab, http_client)
    argocd_collector = ArgoCDCollector(settings.argocd.instances, http_client)
    orchestrator = ScanOrchestrator(gitlab_collector, argocd_collector, storage, settings.argocd.app_name_prefix)
    scheduler = ScanScheduler(orchestrator, settings.scan_interval_seconds)

    app.state.storage = storage
    app.state.http_client = http_client
    app.state.orchestrator = orchestrator
    app.state.scheduler = scheduler

    await scheduler.start()

    # Bootstrap admin user if no users exist and a password is configured
    user_storage = UserJsonStorage(settings.auth.users_json_path)
    if await user_storage.count() == 0 and settings.auth.bootstrap_admin_password:
        admin = UserRecord(
            username=settings.auth.bootstrap_admin_username,
            hashed_password=hash_password(settings.auth.bootstrap_admin_password),
            is_admin=True,
        )
        await user_storage.create_user(admin)
        logger.info("Bootstrap admin user '%s' created", settings.auth.bootstrap_admin_username)

    logger.info("DBaaS backend started")

    yield

    await scheduler.stop()
    await http_client.aclose()
    logger.info("DBaaS backend shut down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="DBaaS Manager",
        description="Aggregates database metadata from GitLab and ArgoCD.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(databases.router, prefix="/api/v1")
    app.include_router(connect.router, prefix="/api/v1")
    app.include_router(scan.router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
