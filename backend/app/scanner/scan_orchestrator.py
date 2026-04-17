from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.collectors.argocd_collector import ArgoCDCollector
from app.collectors.gitlab_collector import GitLabCollector
from app.models.database import DatabaseRecord
from app.registry.db_type_registry import DBTypeRegistry
from app.storage.base import ScanMetadata, StorageBackend

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    records_count: int
    duration_seconds: float
    unmatched_argocd_apps: list[str]


class ScanOrchestrator:
    """
    Coordinates the GitLab and ArgoCD collectors, merges their results
    into DatabaseRecord objects, and persists them via the storage backend.

    Merge logic:
        1. Run both collectors concurrently via asyncio.gather.
        2. Build a lookup dict: argocd_app_key → [ArgoAppInfo] from ArgoCD results.
        3. For each RawGitLabDB, derive the expected ArgoCD app name as
           "{argocd_app_prefix}-{project_slug}" (e.g. "dbaas-analytics-pg") and
           look it up in the map.
        4. Any ArgoCD apps with no matching GitLab project are logged as
           unmatched (stored in ScanMetadata for operator visibility).
    """

    def __init__(
        self,
        gitlab_collector: GitLabCollector,
        argocd_collector: ArgoCDCollector,
        storage: StorageBackend,
        argocd_app_prefix: str = "dbaas",
    ) -> None:
        self._gitlab = gitlab_collector
        self._argocd = argocd_collector
        self._storage = storage
        self._argocd_app_prefix = argocd_app_prefix

    async def run(self) -> ScanResult:
        await self._storage.set_scan_metadata(
            ScanMetadata(status="running", last_scan_at=datetime.now(timezone.utc))
        )

        start = asyncio.get_running_loop().time()
        try:
            gitlab_dbs, argocd_app_map = await asyncio.gather(
                self._gitlab.collect(),
                self._argocd.collect(),
            )
        except Exception as exc:
            await self._storage.set_scan_metadata(
                ScanMetadata(
                    status="error",
                    last_scan_at=datetime.now(timezone.utc),
                    error_message=str(exc),
                )
            )
            raise

        # Track which ArgoCD app keys were matched
        matched_keys: set[str] = set()
        records: list[DatabaseRecord] = []

        for db in gitlab_dbs:
            # ArgoCD app name convention: "{ARGOCD_APP_NAME_PREFIX}-{project_slug}"
            # e.g. prefix="dbaas", project_slug="analytics-pg" → "dbaas-analytics-pg"
            app_key = f"{self._argocd_app_prefix}-{db.project_slug}" if self._argocd_app_prefix else db.project_slug
            argocd_apps = argocd_app_map.get(app_key, [])

            if argocd_apps:
                matched_keys.add(app_key)
            else:
                logger.debug(
                    "No ArgoCD match for GitLab project '%s' (tried key: '%s')",
                    db.project_slug,
                    app_key,
                )

            records.append(
                DatabaseRecord(
                    **{
                        "_id": f"gitlab-project-{db.project_id}",
                        "db_type": db.db_type,
                        "db_name": db.db_name,
                        "group": db.group,
                        "gitlab_project_id": db.project_id,
                        "gitlab_project_url": db.project_url,
                        "gitlab_namespace": db.namespace,
                        "chart_version": db.chart_version,
                        "chart_name": db.chart_name,
                        "argocd_apps": argocd_apps,
                    }
                )
            )

        unmatched = [key for key in argocd_app_map if key not in matched_keys]
        if unmatched:
            sample = unmatched[:10]
            logger.warning(
                "%d ArgoCD app(s) had no matching GitLab project (showing up to 10): %s%s",
                len(unmatched),
                sample,
                " …" if len(unmatched) > 10 else "",
            )

        await self._storage.upsert_many(records)
        await self._refresh_parent_chart_versions()

        duration = asyncio.get_running_loop().time() - start
        logger.info(
            "Scan complete: %d databases, %d unmatched ArgoCD apps, %.1fs",
            len(records),
            len(unmatched),
            duration,
        )

        await self._storage.set_scan_metadata(
            ScanMetadata(status="ok", last_scan_at=datetime.now(timezone.utc))
        )

        return ScanResult(
            records_count=len(records),
            duration_seconds=duration,
            unmatched_argocd_apps=unmatched,
        )


    async def _refresh_parent_chart_versions(self) -> None:
        """Fetch the current version of each registered parent helm chart from GitLab."""
        descriptors = [d for d in DBTypeRegistry.all_types() if d.helm_chart_url]
        if not descriptors:
            return

        tasks = [self._gitlab.fetch_chart_version_from_url(d.helm_chart_url) for d in descriptors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for descriptor, result in zip(descriptors, results):
            if isinstance(result, Exception):
                logger.warning(
                    "Failed to fetch parent chart version for %s: %s",
                    descriptor.canonical_name,
                    result,
                )
            elif result:
                descriptor.helm_chart_version = result
                logger.info(
                    "Parent chart version for %s: %s",
                    descriptor.canonical_name,
                    result,
                )


class ScanScheduler:
    """
    Runs ScanOrchestrator on a fixed interval in the background.

    - Uses a single asyncio task to avoid overlapping scans.
    - `trigger_now()` is safe to call concurrently; it no-ops if a scan
      is already in progress.
    - Manual triggers wake the sleeping loop without resetting the periodic
      schedule — the next auto-scan fires at the originally scheduled time.
    """

    def __init__(self, orchestrator: ScanOrchestrator, interval_seconds: int) -> None:
        self._orchestrator = orchestrator
        self._interval = interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._running = asyncio.Event()
        self._trigger = asyncio.Event()

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop(run_immediately=True), name="scan-scheduler")
        logger.info("Scan scheduler started (interval=%ds)", self._interval)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scan scheduler stopped")

    async def trigger_now(self) -> None:
        """Request an immediate scan. No-ops if one is already running."""
        if self._running.is_set():
            logger.debug("Scan already in progress, ignoring trigger_now()")
            return
        self._trigger.set()

    async def _sleep_or_trigger(self) -> None:
        """Sleep for the configured interval, but wake early if trigger_now() fires."""
        try:
            await asyncio.wait_for(self._trigger.wait(), timeout=self._interval)
        except asyncio.TimeoutError:
            pass

    async def _loop(self, run_immediately: bool = False) -> None:
        if not run_immediately:
            await self._sleep_or_trigger()

        while True:
            self._running.set()
            self._trigger.clear()
            try:
                await self._orchestrator.run()
            except Exception:
                logger.exception("Scan raised an unhandled exception")
            finally:
                self._running.clear()
            await self._sleep_or_trigger()
