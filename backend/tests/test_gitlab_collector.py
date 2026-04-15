from __future__ import annotations

import httpx
import pytest
import respx

import app.registry.types  # noqa: F401
from app.collectors.gitlab_collector import GitLabCollector
from app.config import GitLabSettings


def make_settings() -> GitLabSettings:
    return GitLabSettings(
        url="https://gitlab.example.com",
        token="test-token",
        parent_group_id=10,
        request_concurrency=5,
    )


CHART_YAML_POSTGRESQL = """\
name: users-db
version: 1.0.0
annotations:
  dbaas/db-type: postgresql
"""

CHART_YAML_NO_ANNOTATION = """\
name: mystery-db
version: 2.0.0
"""


@respx.mock
async def test_collect_happy_path() -> None:
    respx.get("https://gitlab.example.com/api/v4/groups/10/subgroups").mock(
        return_value=httpx.Response(
            200,
            json=[{"id": 20, "full_path": "dbaas/ops", "name": "ops"}],
            headers={"X-Next-Page": ""},
        )
    )
    # subgroups of subgroup 20 (leaf, no children)
    respx.get("https://gitlab.example.com/api/v4/groups/20/subgroups").mock(
        return_value=httpx.Response(200, json=[], headers={"X-Next-Page": ""})
    )
    respx.get("https://gitlab.example.com/api/v4/groups/20/projects").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 100,
                    "path": "users-db",
                    "web_url": "https://gitlab.example.com/dbaas/ops/users-db",
                }
            ],
            headers={"X-Next-Page": ""},
        )
    )
    respx.get(
        "https://gitlab.example.com/api/v4/projects/100/repository/files/Chart.yaml/raw?ref=main"
    ).mock(return_value=httpx.Response(200, text=CHART_YAML_POSTGRESQL))

    async with httpx.AsyncClient() as client:
        collector = GitLabCollector(make_settings(), client)
        dbs = await collector.collect()

    assert len(dbs) == 1
    assert dbs[0].db_name == "users-db"
    assert dbs[0].db_type == "postgresql"
    assert dbs[0].chart_version == "1.0.0"
    assert dbs[0].namespace == "dbaas/ops"


@respx.mock
async def test_collect_skips_missing_annotation() -> None:
    respx.get("https://gitlab.example.com/api/v4/groups/10/subgroups").mock(
        return_value=httpx.Response(200, json=[], headers={"X-Next-Page": ""})
    )
    # No subgroups → no projects → empty result
    async with httpx.AsyncClient() as client:
        collector = GitLabCollector(make_settings(), client)
        dbs = await collector.collect()
    assert dbs == []


@respx.mock
async def test_chart_yaml_404_returns_none() -> None:
    respx.get(
        "https://gitlab.example.com/api/v4/projects/999/repository/files/Chart.yaml/raw?ref=main"
    ).mock(return_value=httpx.Response(404))

    from app.collectors.gitlab_collector import ProjectInfo

    project = ProjectInfo(
        id=999,
        name="ghost-db",
        web_url="https://gitlab.example.com/dbaas/ops/ghost-db",
        namespace_full_path="dbaas/ops",
    )
    async with httpx.AsyncClient() as client:
        collector = GitLabCollector(make_settings(), client)
        result = await collector._fetch_chart_yaml(project)
    assert result is None
