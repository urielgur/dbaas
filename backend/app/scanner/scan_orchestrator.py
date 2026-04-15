from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.collectors.argocd_collector import ArgoCDCollector
from app.collectors.gitlab_collector import GitLabCollector
from app.models.database import DatabaseRecord
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
        3. For each RawGitLabDB, derive the expected app key
           (via ArgoCDCollector.build_app_key) and attach matching apps.
        4. Any ArgoCD apps with no matching GitLab project are logged as
           unmatched (stored in ScanMetadata for operator visibility).
    """

    def __init__(
        self,
        gitlab_collector: GitLabCollector,
        argocd_collector: ArgoCDCollector,
        storage: StorageBackend,
    ) -> None:
        self._gitlab = gitlab_collector
        self._argocd = argocd_collector
        self._storage = storage

    async def run(self) -> ScanResult:
        await self._storage.set_scan_metadata(
            ScanMetadata(status="running", last_scan_at=datetime.now(timezone.utc))
        )

        start = asyncio.get_event_loop().time()
        try:
            gitlab_dbs, argocd_app_map = await asyncio.gather(
                self._gitlab.collect(),
                self._argocd.collect(),
            )
        except Exception as exc:
            logger.exception("Scan failed during collection phase")
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
            app_key = ArgoCDCollector.build_app_key(db.namespace, db.db_name)
            argocd_apps = argocd_app_map.get(app_key, [])
            if argocd_apps:
                matched_keys.add(app_key)

            records.append(
                DatabaseRecord(
                    **{
                        "_id": f"gitlab-project-{db.project_id}",
                        "db_type": db.db_type,
                        "db_name": db.db_name,
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
            logger.warning(
                "%d ArgoCD app(s) had no matching GitLab project: %s",
                len(unmatched),
                unmatched,
            )

        await self._storage.upsert_many(records)

        duration = asyncio.get_event_loop().time() - start
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


class ScanScheduler:
    """
    Runs ScanOrchestrator on a fixed interval in the background.

    - Uses a single asyncio task to avoid overlapping scans.
    - `trigger_now()` is safe to call concurrently; it no-ops if a scan
      is already in progress.
    """

    def __init__(self, orchestrator: ScanOrchestrator, interval_seconds: int) -> None:
        self._orchestrator = orchestrator
        self._interval = interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._running = asyncio.Event()

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop(), name="scan-scheduler")
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
        if self._task:
            self._task.cancel()
        self._task = asyncio.create_task(self._loop(run_immediately=True), name="scan-scheduler")

    async def _loop(self, run_immediately: bool = False) -> None:
        if not run_immediately:
            await asyncio.sleep(self._interval)

        while True:
            self._running.set()
            try:
                await self._orchestrator.run()
            except Exception:
                logger.exception("Scan raised an unhandled exception")
            finally:
                self._running.clear()
            await asyncio.sleep(self._interval)
