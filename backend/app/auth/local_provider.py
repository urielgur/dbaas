from __future__ import annotations

from passlib.context import CryptContext

from app.auth.provider import AuthProvider
from app.models.user import UserRecord
from app.storage.user_storage import UserJsonStorage

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


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
