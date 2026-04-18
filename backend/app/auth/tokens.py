from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from pydantic import BaseModel

from app.config import settings


class TokenData(BaseModel):
    sub: str


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.auth.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.auth.secret_key, algorithm=settings.auth.algorithm)


def decode_access_token(token: str) -> TokenData | None:
    try:
        payload = jwt.decode(
            token, settings.auth.secret_key, algorithms=[settings.auth.algorithm]
        )
        sub: str | None = payload.get("sub")
        if sub is None:
            return None
        return TokenData(sub=sub)
    except jwt.PyJWTError:
        return None
