from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import get_current_user, get_storage
from app.models.api import ListResponse
from app.models.database import DatabaseRecord
from app.models.user import UserRecord
from app.registry.db_type_registry import DBTypeRegistry
from app.storage.base import StorageBackend

router = APIRouter(prefix="/databases", tags=["databases"])

_SORTABLE_FIELDS = frozenset({"db_type", "db_name", "group", "chart_version", "last_scanned_at"})


def _sort_key(record: DatabaseRecord, field: str) -> str | int | float:
    val = getattr(record, field, None)
    if val is None:
        return ""
    if isinstance(val, str):
        return val.lower()
    return val  # type: ignore[return-value]


@router.get("", response_model=ListResponse)
async def list_databases(
    _: Annotated[UserRecord, Depends(get_current_user)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
    db_type: str | None = Query(default=None, description="Filter by DB type"),
    namespace: str | None = Query(default=None, description="Filter by GitLab namespace"),
    group: str | None = Query(default=None, description="Filter by group"),
    cluster: str | None = Query(default=None, description="Filter by ArgoCD cluster"),
    q: str | None = Query(default=None, description="Substring search on db_name"),
    limit: int = Query(default=50, ge=1, le=1000, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    sort_by: str | None = Query(default=None, description="Field to sort by"),
    sort_dir: Literal["asc", "desc"] = Query(default="asc", description="Sort direction"),
) -> ListResponse:
    records = await storage.get_all()
    meta = await storage.get_scan_metadata()

    if db_type:
        records = [r for r in records if r.db_type == db_type]
    if namespace:
        records = [r for r in records if r.gitlab_namespace == namespace]
    if group:
        records = [r for r in records if r.group == group]
    if cluster:
        records = [r for r in records if any(a.cluster == cluster for a in r.argocd_apps)]
    if q:
        q_lower = q.lower()
        records = [r for r in records if q_lower in r.db_name.lower()]

    total = len(records)

    if sort_by:
        if sort_by not in _SORTABLE_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_by field '{sort_by}'. Allowed: {sorted(_SORTABLE_FIELDS)}",
            )
        records.sort(
            key=lambda r: _sort_key(r, sort_by),
            reverse=(sort_dir == "desc"),
        )

    records = records[offset : offset + limit]

    return ListResponse(
        items=[r.model_dump_api() for r in records],
        total=total,
        last_scanned_at=meta.last_scan_at,
    )


@router.get("/groups")
async def list_groups(
    _: Annotated[UserRecord, Depends(get_current_user)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> list[str]:
    records = await storage.get_all()
    return sorted({r.group for r in records if r.group})


@router.get("/clusters")
async def list_clusters(
    _: Annotated[UserRecord, Depends(get_current_user)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> list[str]:
    records = await storage.get_all()
    return sorted({a.cluster for r in records for a in r.argocd_apps if a.cluster})


@router.get("/types")
async def list_db_types(
    _: Annotated[UserRecord, Depends(get_current_user)],
) -> list[dict[str, str]]:
    return [
        {
            "canonical_name": d.canonical_name,
            "display_label": d.display_label,
            "icon_name": d.icon_name,
            "console_url_template": settings.console.get_template(d.canonical_name),
            "helm_chart_url": d.helm_chart_url,
            "helm_chart_version": d.helm_chart_version,
        }
        for d in DBTypeRegistry.all_types()
    ]


@router.get("/{db_id}")
async def get_database(
    db_id: str,
    _: Annotated[UserRecord, Depends(get_current_user)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> dict:
    record = await storage.get_by_id(db_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Database not found")
    return record.model_dump_api()


class NotesUpdate(BaseModel):
    notes: str = Field(max_length=10000)


@router.patch("/{db_id}/notes")
async def update_notes(
    db_id: str,
    body: NotesUpdate,
    _: Annotated[UserRecord, Depends(get_current_user)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> dict:
    found = await storage.update_notes(db_id, body.notes)
    if not found:
        raise HTTPException(status_code=404, detail="Database not found")
    return {"ok": True}
