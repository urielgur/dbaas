from __future__ import annotations

from app.models.database import DatabaseRecord
from app.storage.base import ScanMetadata, StorageBackend

_NOT_CONFIGURED = (
    "MongoDB storage is not yet wired. "
    "Install `motor` and set STORAGE_BACKEND=mongodb and MONGO_URI in your environment."
)


class MongoStorageBackend(StorageBackend):
    """
    MongoDB implementation using motor (async driver).

    To activate:
    1. pip install motor
    2. Set STORAGE_BACKEND=mongodb and MONGO_URI=mongodb://... in .env
    3. Replace the NotImplementedError bodies below with real motor calls.

    Collection: `databases` — each document is a DatabaseRecord serialized with _id.
    Scan metadata lives in a separate `scan_metadata` collection (single document).
    """

    def __init__(self, uri: str, database: str = "dbaas") -> None:
        try:
            import motor.motor_asyncio
        except ImportError as e:
            raise ImportError(
                "motor is required for MongoDB storage. Run: pip install motor"
            ) from e
        client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self._records = client[database]["databases"]

    async def update_notes(self, record_id: str, notes: str) -> bool:
        result = await self._records.update_one(
            {"_id": record_id},
            {"$set": {"notes": notes}},
        )
        return result.matched_count > 0

    async def get_all(self) -> list[DatabaseRecord]:
        raise NotImplementedError(_NOT_CONFIGURED)

    async def get_by_id(self, record_id: str) -> DatabaseRecord | None:
        raise NotImplementedError(_NOT_CONFIGURED)

    async def upsert_many(self, records: list[DatabaseRecord]) -> None:
        raise NotImplementedError(_NOT_CONFIGURED)

    async def get_scan_metadata(self) -> ScanMetadata:
        raise NotImplementedError(_NOT_CONFIGURED)

    async def set_scan_metadata(self, meta: ScanMetadata) -> None:
        raise NotImplementedError(_NOT_CONFIGURED)
