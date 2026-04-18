from __future__ import annotations

import bcrypt

from app.auth.provider import AuthProvider
from app.models.user import UserRecord
from app.storage.user_storage import UserJsonStorage

# Used for constant-time dummy checks when a username does not exist,
# preventing timing-based username enumeration attacks.
_DUMMY_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt()).decode()


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
            # Run a dummy check to keep response time constant regardless of
            # whether the username exists, preventing enumeration via timing.
            verify_password(password, _DUMMY_HASH)
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
