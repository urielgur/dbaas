from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SyncStats(BaseModel):
    synced: int = 0
    out_of_sync: int = 0
    unknown: int = 0


class ArgoAppInfo(BaseModel):
    cluster: str
    argocd_url: str
    app_name: str
    app_url: str
    sync_status: str  # "Synced" | "OutOfSync" | "Unknown"
    health_status: str  # "Healthy" | "Degraded" | "Progressing" | "Missing" | "Unknown"
    sync_stats: SyncStats


class DatabaseRecord(BaseModel):
    """
    Canonical representation of a managed database.

    The `id` field uses `_id` as its serialization alias so it maps
    directly to MongoDB's primary key convention — no migration needed
    when switching storage backends.

    `extra_fields` is an open dict for ad-hoc data that doesn't yet
    warrant a first-class field, providing forward compatibility.
    """

    id: str = Field(alias="_id")
    db_type: str
    db_name: str
    group: str  # last segment of the GitLab namespace, e.g. "data"
    gitlab_project_id: int
    gitlab_project_url: str
    gitlab_namespace: str  # full namespace path, e.g. "dbaas/data"
    chart_version: str
    chart_name: str
    argocd_apps: list[ArgoAppInfo] = []
    extra_fields: dict[str, Any] = {}
    notes: str = ""
    last_scanned_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(populate_by_name=True)

    def model_dump_api(self) -> dict[str, Any]:
        """Serialize for API responses (uses `id` not `_id`)."""
        data = self.model_dump(by_alias=False)
        return data
