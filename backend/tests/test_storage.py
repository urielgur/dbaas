from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.models.database import DatabaseRecord
from app.storage.base import ScanMetadata
from app.storage.json_storage import JsonStorageBackend


@pytest.fixture
def tmp_storage(tmp_path: Path) -> JsonStorageBackend:
    return JsonStorageBackend(tmp_path / "databases.json")


async def test_get_all_empty(tmp_storage: JsonStorageBackend) -> None:
    assert await tmp_storage.get_all() == []


async def test_upsert_and_get_all(
    tmp_storage: JsonStorageBackend, sample_record: DatabaseRecord
) -> None:
    await tmp_storage.upsert_many([sample_record])
    records = await tmp_storage.get_all()
    assert len(records) == 1
    assert records[0].db_name == "ops-users-db"


async def test_upsert_is_idempotent(
    tmp_storage: JsonStorageBackend, sample_record: DatabaseRecord
) -> None:
    await tmp_storage.upsert_many([sample_record])
    await tmp_storage.upsert_many([sample_record])
    records = await tmp_storage.get_all()
    assert len(records) == 1


async def test_get_by_id(
    tmp_storage: JsonStorageBackend, sample_record: DatabaseRecord
) -> None:
    await tmp_storage.upsert_many([sample_record])
    found = await tmp_storage.get_by_id("gitlab-project-1")
    assert found is not None
    assert found.db_type == "postgresql"


async def test_get_by_id_missing(tmp_storage: JsonStorageBackend) -> None:
    assert await tmp_storage.get_by_id("does-not-exist") is None


async def test_scan_metadata_roundtrip(tmp_storage: JsonStorageBackend) -> None:
    from datetime import datetime, timezone

    meta = ScanMetadata(status="ok", last_scan_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    await tmp_storage.set_scan_metadata(meta)
    loaded = await tmp_storage.get_scan_metadata()
    assert loaded.status == "ok"
    assert loaded.last_scan_at is not None
    assert loaded.last_scan_at.year == 2026


async def test_atomic_write_creates_dirs(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "databases.json"
    storage = JsonStorageBackend(nested)
    await storage.upsert_many([])
    assert nested.exists()
