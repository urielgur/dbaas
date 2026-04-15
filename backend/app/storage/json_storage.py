from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.database import DatabaseRecord
from app.storage.base import ScanMetadata, StorageBackend

_SENTINEL = "never"


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _serialize_dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


class JsonStorageBackend(StorageBackend):
    """
    Stores all data in a single JSON file:

        {
            "scan_metadata": { "status": "ok", "last_scan_at": "...", "error_message": null },
            "records": [ ...DatabaseRecord dicts with _id key... ]
        }

    Writes are atomic (write to .tmp then os.replace) and protected by an
    asyncio.Lock to prevent concurrent corruption.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_raw(self) -> dict[str, Any]:
        if not self._path.exists():
            return {"scan_metadata": {"status": _SENTINEL}, "records": []}
        with self._path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_raw(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp, self._path)

    # ------------------------------------------------------------------
    # StorageBackend interface
    # ------------------------------------------------------------------

    async def get_all(self) -> list[DatabaseRecord]:
        async with self._lock:
            raw = self._read_raw()
        return [
            DatabaseRecord.model_validate(r) for r in raw.get("records", [])
        ]

    async def get_by_id(self, record_id: str) -> DatabaseRecord | None:
        async with self._lock:
            raw = self._read_raw()
        for r in raw.get("records", []):
            if r.get("_id") == record_id:
                return DatabaseRecord.model_validate(r)
        return None

    async def upsert_many(self, records: list[DatabaseRecord]) -> None:
        async with self._lock:
            raw = self._read_raw()
            # Build index from existing records for O(1) merge
            existing: dict[str, dict[str, Any]] = {
                r["_id"]: r for r in raw.get("records", []) if "_id" in r
            }
            for record in records:
                serialized = json.loads(record.model_dump_json(by_alias=True))
                existing[serialized["_id"]] = serialized
            raw["records"] = list(existing.values())
            self._write_raw(raw)

    async def get_scan_metadata(self) -> ScanMetadata:
        async with self._lock:
            raw = self._read_raw()
        meta = raw.get("scan_metadata", {})
        return ScanMetadata(
            status=meta.get("status", _SENTINEL),
            last_scan_at=_parse_dt(meta.get("last_scan_at")),
            error_message=meta.get("error_message"),
        )

    async def set_scan_metadata(self, meta: ScanMetadata) -> None:
        async with self._lock:
            raw = self._read_raw()
            raw["scan_metadata"] = {
                "status": meta.status,
                "last_scan_at": _serialize_dt(meta.last_scan_at),
                "error_message": meta.error_message,
            }
            self._write_raw(raw)
