from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.clients.openshift_client import (
    apply_template,
    fetch_secret_fields,
    needs_secret,
)
from app.config import settings
from app.dependencies import get_current_user, get_storage
from app.models.user import UserRecord
from app.storage.base import StorageBackend

router = APIRouter(prefix="/databases", tags=["connect"])


class ConnectResult(BaseModel):
    cluster: str
    url: str


@router.get("/{db_id}/connect", response_model=list[ConnectResult])
async def get_connect_urls(
    db_id: str,
    _: Annotated[UserRecord, Depends(get_current_user)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
    cluster: str | None = Query(default=None, description="Limit to one cluster"),
) -> list[ConnectResult]:
    """
    Build connection URL(s) for a database, resolving credentials from OpenShift
    secrets where the template requires them.

    Returns one entry per deployed cluster (or just the requested cluster).
    """
    record = await storage.get_by_id(db_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Database not found")

    template = settings.console.get_template(record.db_type)
    if not template:
        raise HTTPException(
            status_code=400,
            detail=f"No console URL template configured for db type '{record.db_type}'",
        )

    apps = record.argocd_apps
    if cluster:
        apps = [a for a in apps if a.cluster == cluster]
    if not apps:
        raise HTTPException(status_code=404, detail="No matching deployed clusters found")

    base_vars = {
        "db_name": record.db_name,
        "group": record.group,
        "db_type": record.db_type,
    }

    results: list[ConnectResult] = []

    async with httpx.AsyncClient(timeout=10.0, verify=False) as http_client:
        for app in apps:
            cluster_vars = {**base_vars, "cluster": app.cluster}

            if needs_secret(template):
                os_cluster = settings.openshift.get_cluster(app.cluster)
                if os_cluster is None:
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            f"No OpenShift config for cluster '{app.cluster}'. "
                            f"Set OPENSHIFT_CLUSTERS in .env."
                        ),
                    )

                namespace = apply_template(
                    settings.openshift.secret_namespace_template, cluster_vars
                )
                secret_name = apply_template(
                    settings.openshift.secret_name_template, cluster_vars
                )

                try:
                    creds = await fetch_secret_fields(
                        cluster=os_cluster,
                        namespace=namespace,
                        secret_name=secret_name,
                        fields=[
                            settings.openshift.username_field,
                            settings.openshift.password_field,
                            settings.openshift.host_field,
                            settings.openshift.port_field,
                        ],
                        http_client=http_client,
                    )
                except RuntimeError as exc:
                    raise HTTPException(status_code=502, detail=str(exc)) from exc

                cluster_vars.update(
                    {
                        "username": creds.get(settings.openshift.username_field, ""),
                        "password": creds.get(settings.openshift.password_field, ""),
                        "host": creds.get(settings.openshift.host_field, ""),
                        "port": creds.get(settings.openshift.port_field, "27017"),
                    }
                )

            results.append(
                ConnectResult(
                    cluster=app.cluster,
                    url=apply_template(template, cluster_vars),
                )
            )

    return results
