from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from app.models.user import UserRecord


class UserJsonStorage:
    """
    Stores users in a single JSON file:

        { "users": [ ...UserRecord dicts... ] }

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
            return {"users": []}
        with self._path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_raw(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp, self._path)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def get_user(self, username: str) -> UserRecord | None:
        async with self._lock:
            raw = self._read_raw()
        for u in raw.get("users", []):
            if u.get("username") == username:
                return UserRecord.model_validate(u)
        return None

    async def create_user(self, record: UserRecord) -> None:
        async with self._lock:
            raw = self._read_raw()
            users: list[dict[str, Any]] = raw.get("users", [])
            users.append(json.loads(record.model_dump_json()))
            raw["users"] = users
            self._write_raw(raw)

    async def list_users(self) -> list[UserRecord]:
        async with self._lock:
            raw = self._read_raw()
        return [UserRecord.model_validate(u) for u in raw.get("users", [])]

    async def count(self) -> int:
        async with self._lock:
            raw = self._read_raw()
        return len(raw.get("users", []))
