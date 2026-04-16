from __future__ import annotations

import bcrypt

from app.auth.provider import AuthProvider
from app.models.user import UserRecord
from app.storage.user_storage import UserJsonStorage


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


class LocalAuthProvider(AuthProvider):
    def __init__(self, storage: UserJsonStorage) -> None:
        self._storage = storage

    async def authenticate(self, username: str, password: str) -> UserRecord | None:
        user = await self._storage.get_user(username)
        if user is None:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
