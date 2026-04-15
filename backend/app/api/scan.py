from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends

from app.dependencies import get_current_user, get_scheduler, get_storage
from app.models.api import ScanStatusResponse
from app.models.user import UserRecord
from app.scanner.scan_orchestrator import ScanScheduler
from app.storage.base import StorageBackend

router = APIRouter(prefix="/scan", tags=["scan"])


@router.post("", status_code=202)
async def trigger_scan(
    background_tasks: BackgroundTasks,
    _: Annotated[UserRecord, Depends(get_current_user)],
    scheduler: Annotated[ScanScheduler, Depends(get_scheduler)],
) -> dict[str, str]:
    background_tasks.add_task(scheduler.trigger_now)
    return {"status": "accepted", "message": "Scan triggered"}


@router.get("/status", response_model=ScanStatusResponse)
async def scan_status(
    _: Annotated[UserRecord, Depends(get_current_user)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> ScanStatusResponse:
    meta = await storage.get_scan_metadata()
    return ScanStatusResponse(
        status=meta.status,
        last_scan_at=meta.last_scan_at,
        error_message=meta.error_message,
    )
