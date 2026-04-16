from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Trigger DB type registration before anything else runs
import app.registry.types  # noqa: F401

from app.api import auth, databases, scan
from app.auth.local_provider import hash_password
from app.collectors.argocd_collector import ArgoCDCollector
from app.collectors.gitlab_collector import GitLabCollector
from app.config import settings
from app.dependencies import get_storage
from app.models.user import UserRecord
from app.scanner.scan_orchestrator import ScanOrchestrator, ScanScheduler
from app.storage.user_storage import UserJsonStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Shared HTTP client — one connection pool for all collectors
    http_client = httpx.AsyncClient(timeout=30.0)

    storage = get_storage()
    gitlab_collector = GitLabCollector(settings.gitlab, http_client)
    argocd_collector = ArgoCDCollector(settings.argocd.instances, http_client)
    orchestrator = ScanOrchestrator(gitlab_collector, argocd_collector, storage, settings.argocd.app_name_prefix)
    scheduler = ScanScheduler(orchestrator, settings.scan_interval_seconds)

    app.state.orchestrator = orchestrator
    app.state.scheduler = scheduler

    await scheduler.start()

    # Bootstrap admin user if no users exist and a password is configured
    if not settings.auth.secret_key:
        logger.warning("AUTH_SECRET_KEY is not set — tokens are signed with an empty key (insecure)")
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
    app.include_router(scan.router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
