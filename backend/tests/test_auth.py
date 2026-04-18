from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import jwt as pyjwt
import pytest

from app.auth.local_provider import LocalAuthProvider, hash_password
from app.auth.tokens import create_access_token, decode_access_token
from app.models.user import UserRecord


def make_user(username: str = "alice", password: str = "secret") -> UserRecord:
    return UserRecord(
        username=username,
        hashed_password=hash_password(password),
        is_admin=False,
    )


# ── LocalAuthProvider ─────────────────────────────────────────────────────────

async def test_authenticate_valid_credentials() -> None:
    user = make_user("alice", "secret")
    storage = AsyncMock()
    storage.get_user.return_value = user

    result = await LocalAuthProvider(storage).authenticate("alice", "secret")
    assert result is not None
    assert result.username == "alice"


async def test_authenticate_wrong_password() -> None:
    user = make_user("alice", "secret")
    storage = AsyncMock()
    storage.get_user.return_value = user

    result = await LocalAuthProvider(storage).authenticate("alice", "wrongpassword")
    assert result is None


async def test_authenticate_unknown_user() -> None:
    storage = AsyncMock()
    storage.get_user.return_value = None

    result = await LocalAuthProvider(storage).authenticate("ghost", "anything")
    assert result is None


# ── Token helpers ─────────────────────────────────────────────────────────────

def test_create_and_decode_token_roundtrip() -> None:
    token = create_access_token("bob")
    assert isinstance(token, str)
    data = decode_access_token(token)
    assert data is not None
    assert data.sub == "bob"


def test_decode_invalid_token_returns_none() -> None:
    assert decode_access_token("not.a.valid.jwt") is None


def test_decode_garbage_returns_none() -> None:
    assert decode_access_token("") is None


def test_decode_expired_token_returns_none() -> None:
    from app.config import settings

    key = settings.auth.secret_key
    if not key:
        pytest.skip("AUTH_SECRET_KEY not configured — cannot test expiry")

    expired_token = pyjwt.encode(
        {"sub": "alice", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        key,
        algorithm=settings.auth.algorithm,
    )
    assert decode_access_token(expired_token) is None
