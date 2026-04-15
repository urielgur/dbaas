from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.user import UserRecord


class AuthProvider(ABC):
    """
    Pluggable authentication backend.

    Implement this ABC to support additional identity sources.
    The current implementation is LocalAuthProvider (bcrypt + JSON storage).
    To add Windows Active Directory support later, create ActiveDirectoryAuthProvider
    using ldap3, wire it in get_auth_provider() in dependencies.py — no other
    changes are required.
    """

    @abstractmethod
    async def authenticate(self, username: str, password: str) -> UserRecord | None:
        """
        Return the UserRecord on success, None on bad credentials.
        Raise RuntimeError for infrastructure failures (e.g. LDAP unreachable).
        """
        ...
