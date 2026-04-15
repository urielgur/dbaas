from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from app.models.database import DatabaseRecord


class ListResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    last_scanned_at: datetime | None = None


class ScanStatusResponse(BaseModel):
    status: Literal["ok", "running", "error", "never"]
    last_scan_at: datetime | None = None
    error_message: str | None = None
