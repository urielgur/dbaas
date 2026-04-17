from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import urllib.parse

import httpx
import yaml

from app.config import GitLabSettings
from app.registry.db_type_registry import DBTypeRegistry

logger = logging.getLogger(__name__)


@dataclass
class SubgroupInfo:
    id: int
    full_path: str  # e.g. "dbaas/ops"
    name: str


@dataclass
class ProjectInfo:
    id: int
    name: str
    web_url: str
    namespace_full_path: str  # subgroup path, e.g. "dbaas/ops"
    default_branch: str = "main"


@dataclass
class RawGitLabDB:
    project_id: int
    project_url: str
    namespace: str         # e.g. "dbaas/data"
    group: str             # last segment of namespace, e.g. "data"
    project_slug: str      # GitLab project path slug, e.g. "analytics-pg"
    chart_name: str        # Chart.yaml `name`
    chart_version: str     # dependencies[0].version
    db_type: str           # resolved canonical name from registry
    db_name: str           # project slug by default, or dbaas/db-name annotation override


class GitLabCollector:
    """
    Walks the GitLab subgroup tree under `settings.parent_group_path`,
    discovers all projects (each = one DB), and reads their Chart.yaml.

    Subgroup traversal: BFS, fully paginated. Supports arbitrary nesting depth —
    department subgroups, team sub-subgroups, etc. are all discovered automatically.

    Chart.yaml fields used:
        - `annotations["dbaas/db-type"]`  → db_type  (required; warns if absent)
        - `name`                           → db_name / chart_name
        - `version`                        → chart_version
    """

    def __init__(self, settings: GitLabSettings, http_client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = http_client
        self._semaphore = asyncio.Semaphore(settings.request_concurrency)
        self._base = settings.url.rstrip("/")
        self._headers = {
            "PRIVATE-TOKEN": settings.token,
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def collect(self) -> list[RawGitLabDB]:
        root_id = await self._resolve_group_path(self._settings.parent_group_path)
        subgroups = await self._walk_subgroups(root_id)
        logger.info("Found %d subgroups under '%s'", len(subgroups), self._settings.parent_group_path)

        all_projects: list[ProjectInfo] = []
        project_tasks = [self._get_projects(sg.id, sg.full_path) for sg in subgroups]
        project_lists = await asyncio.gather(*project_tasks)
        for projects in project_lists:
            all_projects.extend(projects)

        logger.info("Found %d projects total", len(all_projects))
        return await self._fetch_all_charts(all_projects)

    # ------------------------------------------------------------------
    # Path resolver
    # ------------------------------------------------------------------

    async def _resolve_group_path(self, path: str) -> int:
        """
        Resolve a group path (e.g. "ugurfinkel-group/dbaas") to its numeric ID.

        The GitLab API accepts URL-encoded paths wherever it expects a group ID,
        so "ugurfinkel-group/dbaas" becomes "ugurfinkel-group%2Fdbaas".
        """
        encoded = urllib.parse.quote(path, safe="")
        url = f"{self._base}/api/v4/groups/{encoded}"
        async with self._semaphore:
            resp = await self._client.get(url, headers=self._headers)
        if resp.status_code == 404:
            raise ValueError(f"GitLab group not found: '{path}'")
        resp.raise_for_status()
        return int(resp.json()["id"])

    # ------------------------------------------------------------------
    # Subgroup traversal (BFS)
    # ------------------------------------------------------------------

    async def _walk_subgroups(self, root_group_id: int) -> list[SubgroupInfo]:
        """
        BFS over the subgroup hierarchy. Returns all subgroups found,
        including the root's direct children and their descendants.
        """
        visited: list[SubgroupInfo] = []
        queue = [root_group_id]

        while queue:
            current_ids = queue[:]
            queue.clear()
            tasks = [self._get_subgroups(gid) for gid in current_ids]
            results = await asyncio.gather(*tasks)
            for subgroup_list in results:
                for sg in subgroup_list:
                    visited.append(sg)
                    queue.append(sg.id)

        return visited

    async def _get_subgroups(self, group_id: int) -> list[SubgroupInfo]:
        return await self._paginate(
            f"{self._base}/api/v4/groups/{group_id}/subgroups",
            params={"per_page": 100},
            parse=lambda item: SubgroupInfo(
                id=item["id"],
                full_path=item["full_path"],
                name=item["name"],
            ),
        )

    # ------------------------------------------------------------------
    # Project listing
    # ------------------------------------------------------------------

    async def _get_projects(self, group_id: int, namespace_path: str) -> list[ProjectInfo]:
        return await self._paginate(
            f"{self._base}/api/v4/groups/{group_id}/projects",
            params={"per_page": 100, "include_subgroups": "false"},
            parse=lambda item: ProjectInfo(
                id=item["id"],
                name=item["path"],  # use `path` (slug), not display name
                web_url=item["web_url"],
                namespace_full_path=namespace_path,
                default_branch=item.get("default_branch") or "main",
            ),
        )

    # ------------------------------------------------------------------
    # Chart.yaml fetching
    # ------------------------------------------------------------------

    async def _fetch_all_charts(self, projects: list[ProjectInfo]) -> list[RawGitLabDB]:
        tasks = [self._fetch_chart_yaml(p) for p in projects]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        dbs: list[RawGitLabDB] = []
        for project, result in zip(projects, results):
            if isinstance(result, Exception):
                logger.warning("Failed to fetch Chart.yaml for project %s: %s", project.name, result)
                continue
            if result is None:
                logger.debug("No Chart.yaml found for project %s", project.name)
                continue
            dbs.append(result)
        return dbs

    async def _fetch_chart_yaml(self, project: ProjectInfo) -> RawGitLabDB | None:
        url = (
            f"{self._base}/api/v4/projects/{project.id}"
            f"/repository/files/Chart.yaml/raw?ref={project.default_branch}"
        )
        async with self._semaphore:
            try:
                resp = await self._client.get(url, headers=self._headers)
            except httpx.HTTPError as exc:
                raise RuntimeError(f"HTTP error fetching Chart.yaml: {exc}") from exc

        if resp.status_code == 404:
            return None
        resp.raise_for_status()

        try:
            chart = yaml.safe_load(resp.text)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"YAML parse error in project {project.name}: {exc}") from exc

        if not isinstance(chart, dict):
            return None

        return self._parse_chart(chart, project)

    def _parse_chart(self, chart: dict[str, Any], project: ProjectInfo) -> RawGitLabDB | None:
        chart_name: str = chart.get("name", project.name)

        dependencies: list[dict] = chart.get("dependencies") or []
        first_dep = dependencies[0] if dependencies else {}
        raw_type = first_dep.get("name", "")
        chart_version: str = str(first_dep.get("version", "unknown"))

        if not raw_type:
            logger.warning(
                "Project %s has no dependencies[0].name in Chart.yaml — skipping",
                project.name,
            )
            return None

        db_type = DBTypeRegistry.resolve(raw_type)
        if db_type == "unknown":
            logger.warning(
                "Unrecognised db type %r in project %s — registered as 'unknown'",
                raw_type,
                project.name,
            )

        annotations: dict[str, str] = chart.get("annotations") or {}
        # db_name defaults to the GitLab project slug; annotation can override it
        db_name = annotations.get("dbaas/db-name", project.name)
        group = project.namespace_full_path.rstrip("/").split("/")[-1]

        return RawGitLabDB(
            project_id=project.id,
            project_url=project.web_url,
            namespace=project.namespace_full_path,
            group=group,
            project_slug=project.name,
            chart_name=chart_name,
            chart_version=chart_version,
            db_type=db_type,
            db_name=db_name,
        )

    # ------------------------------------------------------------------
    # Parent chart version fetching
    # ------------------------------------------------------------------

    async def fetch_chart_version_from_url(self, project_url: str) -> str | None:
        """
        Given a GitLab project web URL (e.g. https://gitlab.example.com/group/my-chart),
        fetch its Chart.yaml and return the `version` field, or None on any failure.
        """
        if not project_url.startswith(self._base):
            logger.warning(
                "helm_chart_url %r does not match GitLab base %r — skipping",
                project_url,
                self._base,
            )
            return None

        project_path = project_url[len(self._base):].lstrip("/")
        encoded_path = urllib.parse.quote(project_path, safe="")
        url = (
            f"{self._base}/api/v4/projects/{encoded_path}"
            f"/repository/files/Chart.yaml/raw?ref=main"
        )

        async with self._semaphore:
            try:
                resp = await self._client.get(url, headers=self._headers)
            except httpx.HTTPError as exc:
                logger.warning("HTTP error fetching parent chart from %r: %s", project_url, exc)
                return None

        if resp.status_code == 404:
            logger.warning("No Chart.yaml found for parent chart at %r", project_url)
            return None
        if not resp.is_success:
            logger.warning(
                "Unexpected status %d fetching parent chart from %r",
                resp.status_code,
                project_url,
            )
            return None

        try:
            chart = yaml.safe_load(resp.text)
        except yaml.YAMLError as exc:
            logger.warning("YAML parse error in parent chart from %r: %s", project_url, exc)
            return None

        if not isinstance(chart, dict):
            return None

        version = chart.get("version")
        return str(version) if version else None

    # ------------------------------------------------------------------
    # Pagination helper
    # ------------------------------------------------------------------

    async def _paginate(
        self,
        url: str,
        params: dict[str, Any],
        parse: Any,
    ) -> list[Any]:
        results: list[Any] = []
        next_page: str | None = "1"

        while next_page:
            async with self._semaphore:
                resp = await self._client.get(
                    url,
                    headers=self._headers,
                    params={**params, "page": next_page},
                )
            resp.raise_for_status()
            for item in resp.json():
                results.append(parse(item))
            next_page = resp.headers.get("X-Next-Page") or None

        return results
