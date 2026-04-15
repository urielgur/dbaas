from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import ArgoCDInstanceConfig
from app.models.database import ArgoAppInfo, SyncStats

logger = logging.getLogger(__name__)


@dataclass
class RawArgoApp:
    name: str
    sync_status: str    # e.g. "Synced", "OutOfSync", "Unknown"
    health_status: str  # e.g. "Healthy", "Degraded", "Progressing", "Missing", "Unknown"
    resources: list[dict[str, Any]]


class ArgoCDCollector:
    """
    Queries all configured ArgoCD instances concurrently and builds a
    mapping of db_name → list[ArgoAppInfo].

    App-to-DB matching is deterministic: given a GitLab project with
    namespace "dbaas/ops" and name "logs-prod", the expected ArgoCD
    app name is "{last_namespace_segment}-{project_name}" = "ops-logs-prod".

    The inverse lookup (app_name → db_name) is performed by stripping
    the cluster-specific suffix from app names. Since the app name IS
    "{subgroup}-{project}", the db_name is derived by looking up the
    known db_names from the GitLab scan and matching against
    "{subgroup}-{db_name}".

    Alternatively, apps are indexed by app_name and the orchestrator
    calls `get_apps_for_db()` with the computed key.
    """

    def __init__(
        self,
        instances: list[ArgoCDInstanceConfig],
        http_client: httpx.AsyncClient,
    ) -> None:
        self._instances = instances
        self._client = http_client

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def collect(self) -> dict[str, list[ArgoAppInfo]]:
        """
        Returns a flat mapping: expected_app_key → list[ArgoAppInfo].

        The expected_app_key is the ArgoCD app name (e.g. "ops-logs-prod").
        The orchestrator constructs this key from GitLab data and looks it up.
        """
        tasks = [self._fetch_instance_apps(instance) for instance in self._instances]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        app_map: dict[str, list[ArgoAppInfo]] = {}
        for instance, result in zip(self._instances, results):
            if isinstance(result, Exception):
                logger.error(
                    "Failed to fetch apps from ArgoCD instance %s: %s",
                    instance.cluster_name,
                    result,
                )
                continue
            for raw_app in result:
                info = self._build_app_info(raw_app, instance)
                app_map.setdefault(raw_app.name, []).append(info)

        return app_map

    # ------------------------------------------------------------------
    # Per-instance fetch
    # ------------------------------------------------------------------

    async def _fetch_instance_apps(self, instance: ArgoCDInstanceConfig) -> list[RawArgoApp]:
        url = f"{instance.url.rstrip('/')}/api/v1/applications"
        headers = {
            "Authorization": f"Bearer {instance.token}",
            "Accept": "application/json",
        }
        try:
            resp = await self._client.get(url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"HTTP error fetching ArgoCD apps from {instance.cluster_name}: {exc}"
            ) from exc

        data = resp.json()
        apps: list[RawArgoApp] = []
        for item in data.get("items") or []:
            apps.append(
                RawArgoApp(
                    name=item["metadata"]["name"],
                    sync_status=item.get("status", {})
                    .get("sync", {})
                    .get("status", "Unknown"),
                    health_status=item.get("status", {})
                    .get("health", {})
                    .get("status", "Unknown"),
                    resources=item.get("status", {}).get("resources") or [],
                )
            )
        return apps

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _build_app_info(
        self, raw: RawArgoApp, instance: ArgoCDInstanceConfig
    ) -> ArgoAppInfo:
        return ArgoAppInfo(
            cluster=instance.cluster_name,
            argocd_url=instance.url,
            app_name=raw.name,
            app_url=f"{instance.url.rstrip('/')}/applications/{raw.name}",
            sync_status=raw.sync_status,
            health_status=raw.health_status,
            sync_stats=self._parse_resource_counts(raw.resources),
        )

    @staticmethod
    def _parse_resource_counts(resources: list[dict[str, Any]]) -> SyncStats:
        """
        Counts resources by sync status from app.status.resources[].

        ArgoCD resource objects have a `status` field ("Synced", "OutOfSync")
        and optionally a `health.status` field. We count by resource sync status.
        """
        synced = 0
        out_of_sync = 0
        unknown = 0
        for resource in resources:
            status = resource.get("status", "").lower()
            if status == "synced":
                synced += 1
            elif status == "outofsync":
                out_of_sync += 1
            else:
                unknown += 1
        return SyncStats(synced=synced, out_of_sync=out_of_sync, unknown=unknown)

    # ------------------------------------------------------------------
    # Key construction (called by orchestrator)
    # ------------------------------------------------------------------

    @staticmethod
    def build_app_key(namespace: str, db_name: str) -> str:
        """
        Derive the expected ArgoCD app name from GitLab data.

        Convention: "{last_namespace_segment}-{db_name}"
        e.g. namespace="dbaas/ops", db_name="logs-prod" → "ops-logs-prod"
        """
        subgroup = namespace.rstrip("/").split("/")[-1]
        return f"{subgroup}-{db_name}"
