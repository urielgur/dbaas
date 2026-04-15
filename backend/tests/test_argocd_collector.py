from __future__ import annotations

import httpx
import respx

from app.collectors.argocd_collector import ArgoCDCollector
from app.config import ArgoCDInstanceConfig


def make_instances() -> list[ArgoCDInstanceConfig]:
    return [
        ArgoCDInstanceConfig(
            cluster_name="cluster-1",
            url="https://argocd1.example.com",
            token="token-1",
        ),
    ]


ARGOCD_RESPONSE = {
    "items": [
        {
            "metadata": {"name": "ops-users-db"},
            "status": {
                "sync": {"status": "Synced"},
                "health": {"status": "Healthy"},
                "resources": [
                    {"status": "Synced"},
                    {"status": "Synced"},
                    {"status": "OutOfSync"},
                ],
            },
        }
    ]
}


@respx.mock
async def test_collect_parses_apps() -> None:
    respx.get("https://argocd1.example.com/api/v1/applications").mock(
        return_value=httpx.Response(200, json=ARGOCD_RESPONSE)
    )

    async with httpx.AsyncClient() as client:
        collector = ArgoCDCollector(make_instances(), client)
        app_map = await collector.collect()

    assert "ops-users-db" in app_map
    apps = app_map["ops-users-db"]
    assert len(apps) == 1
    assert apps[0].sync_status == "Synced"
    assert apps[0].health_status == "Healthy"
    assert apps[0].sync_stats.synced == 2
    assert apps[0].sync_stats.out_of_sync == 1
    assert apps[0].app_url == "https://argocd1.example.com/applications/ops-users-db"


def test_build_app_key() -> None:
    assert ArgoCDCollector.build_app_key("dbaas/ops", "users-db") == "ops-users-db"
    assert ArgoCDCollector.build_app_key("dbaas/data", "logs-prod") == "data-logs-prod"


@respx.mock
async def test_collect_handles_instance_error() -> None:
    respx.get("https://argocd1.example.com/api/v1/applications").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    async with httpx.AsyncClient() as client:
        collector = ArgoCDCollector(make_instances(), client)
        # Should not raise — failed instance is logged and skipped
        app_map = await collector.collect()

    assert app_map == {}
