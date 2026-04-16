from __future__ import annotations

import pytest
import pytest_asyncio

from app.models.database import ArgoAppInfo, DatabaseRecord, SyncStats


@pytest.fixture
def sample_record() -> DatabaseRecord:
    return DatabaseRecord(
        **{
            "_id": "gitlab-project-1",
            "db_type": "postgresql",
            "db_name": "users-db",
            "group": "ops",
            "gitlab_project_id": 1,
            "gitlab_project_url": "https://gitlab.example.com/dbaas/ops/users-db",
            "gitlab_namespace": "dbaas/ops",
            "chart_version": "1.0.0",
            "chart_name": "users-db",
            "argocd_apps": [
                ArgoAppInfo(
                    cluster="cluster-1",
                    argocd_url="https://argocd1.example.com",
                    app_name="ops-users-db",
                    app_url="https://argocd1.example.com/applications/ops-users-db",
                    sync_status="Synced",
                    health_status="Healthy",
                    sync_stats=SyncStats(synced=5, out_of_sync=0, unknown=0),
                )
            ],
        }
    )
