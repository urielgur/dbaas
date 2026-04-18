from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.database import DatabaseRecord


class ScanMetadata(BaseModel):
    status: Literal["ok", "running", "error", "never"] = "never"
    last_scan_at: datetime | None = None
    error_message: str | None = None


class StorageBackend(ABC):
    @abstractmethod
    async def get_all(self) -> list[DatabaseRecord]: ...

    @abstractmethod
    async def get_by_id(self, record_id: str) -> DatabaseRecord | None: ...

    @abstractmethod
    async def upsert_many(self, records: list[DatabaseRecord]) -> None:
        """Replace the full dataset idempotently. Safe to call after every scan."""

    @abstractmethod
    async def update_notes(self, record_id: str, notes: str) -> bool:
        """Update the notes field for a single record. Returns False if not found."""

    @abstractmethod
    async def get_scan_metadata(self) -> ScanMetadata: ...

    @abstractmethod
    async def set_scan_metadata(self, meta: ScanMetadata) -> None: ...
