from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.collectors.gitlab_collector import RawGitLabDB
from app.models.database import ArgoAppInfo, SyncStats
from app.scanner.scan_orchestrator import ScanOrchestrator
from app.storage.json_storage import JsonStorageBackend


def make_raw_db(project_slug: str = "users-db", project_id: int = 1) -> RawGitLabDB:
    return RawGitLabDB(
        project_id=project_id,
        project_url=f"https://gitlab.example.com/dbaas/ops/{project_slug}",
        namespace="dbaas/ops",
        group="ops",
        project_slug=project_slug,
        chart_name=project_slug,
        chart_version="1.0.0",
        db_type="postgresql",
        db_name=project_slug,
    )


def make_argo_app(app_name: str) -> ArgoAppInfo:
    return ArgoAppInfo(
        cluster="cluster-1",
        argocd_url="https://argocd.example.com",
        app_name=app_name,
        app_url=f"https://argocd.example.com/applications/{app_name}",
        sync_status="Synced",
        health_status="Healthy",
        sync_stats=SyncStats(synced=3, out_of_sync=0, unknown=0),
    )


@pytest.fixture
def tmp_storage(tmp_path: Path) -> JsonStorageBackend:
    return JsonStorageBackend(tmp_path / "databases.json")


async def test_run_happy_path(tmp_storage: JsonStorageBackend) -> None:
    gitlab = AsyncMock()
    argocd = AsyncMock()
    gitlab.collect.return_value = [make_raw_db("users-db", 1)]
    argocd.collect.return_value = {"dbaas-users-db": [make_argo_app("dbaas-users-db")]}

    orchestrator = ScanOrchestrator(gitlab, argocd, tmp_storage, argocd_app_prefix="dbaas")
    result = await orchestrator.run()

    assert result.records_count == 1
    assert result.unmatched_argocd_apps == []
    meta = await tmp_storage.get_scan_metadata()
    assert meta.status == "ok"


async def test_run_gitlab_failure(tmp_storage: JsonStorageBackend) -> None:
    gitlab = AsyncMock()
    argocd = AsyncMock()
    gitlab.collect.side_effect = RuntimeError("GitLab unreachable")
    argocd.collect.return_value = {}

    orchestrator = ScanOrchestrator(gitlab, argocd, tmp_storage, argocd_app_prefix="dbaas")
    with pytest.raises(RuntimeError, match="GitLab unreachable"):
        await orchestrator.run()

    meta = await tmp_storage.get_scan_metadata()
    assert meta.status == "error"
    assert "GitLab unreachable" in (meta.error_message or "")


async def test_run_argocd_failure(tmp_storage: JsonStorageBackend) -> None:
    gitlab = AsyncMock()
    argocd = AsyncMock()
    gitlab.collect.return_value = [make_raw_db()]
    argocd.collect.side_effect = RuntimeError("ArgoCD unreachable")

    orchestrator = ScanOrchestrator(gitlab, argocd, tmp_storage, argocd_app_prefix="dbaas")
    with pytest.raises(RuntimeError, match="ArgoCD unreachable"):
        await orchestrator.run()

    meta = await tmp_storage.get_scan_metadata()
    assert meta.status == "error"


async def test_run_partial_argocd_match(tmp_storage: JsonStorageBackend) -> None:
    gitlab = AsyncMock()
    argocd = AsyncMock()
    gitlab.collect.return_value = [
        make_raw_db("users-db", 1),
        make_raw_db("orders-db", 2),
    ]
    argocd.collect.return_value = {
        "dbaas-users-db": [make_argo_app("dbaas-users-db")],
        "dbaas-extra-app": [make_argo_app("dbaas-extra-app")],
    }

    orchestrator = ScanOrchestrator(gitlab, argocd, tmp_storage, argocd_app_prefix="dbaas")
    result = await orchestrator.run()

    assert result.records_count == 2
    assert result.unmatched_argocd_apps == ["dbaas-extra-app"]

    records = await tmp_storage.get_all()
    users_db = next(r for r in records if r.db_name == "users-db")
    orders_db = next(r for r in records if r.db_name == "orders-db")
    assert len(users_db.argocd_apps) == 1
    assert len(orders_db.argocd_apps) == 0
