from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_storage
from app.models.api import ListResponse
from app.models.database import DatabaseRecord
from app.registry.db_type_registry import DBTypeRegistry
from app.storage.base import StorageBackend

router = APIRouter(prefix="/databases", tags=["databases"])


@router.get("", response_model=ListResponse)
async def list_databases(
    storage: Annotated[StorageBackend, Depends(get_storage)],
    db_type: str | None = Query(default=None, description="Filter by DB type"),
    namespace: str | None = Query(default=None, description="Filter by GitLab namespace"),
    q: str | None = Query(default=None, description="Substring search on db_name"),
) -> ListResponse:
    records = await storage.get_all()
    meta = await storage.get_scan_metadata()

    if db_type:
        records = [r for r in records if r.db_type == db_type]
    if namespace:
        records = [r for r in records if r.gitlab_namespace == namespace]
    if q:
        q_lower = q.lower()
        records = [r for r in records if q_lower in r.db_name.lower()]

    return ListResponse(
        items=[r.model_dump_api() for r in records],
        total=len(records),
        last_scanned_at=meta.last_scan_at,
    )


@router.get("/types")
async def list_db_types() -> list[dict[str, str]]:
    return [
        {
            "canonical_name": d.canonical_name,
            "display_label": d.display_label,
            "icon_name": d.icon_name,
        }
        for d in DBTypeRegistry.all_types()
    ]


@router.get("/{db_id}")
async def get_database(
    db_id: str,
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> dict:
    record = await storage.get_by_id(db_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Database not found")
    return record.model_dump_api()
