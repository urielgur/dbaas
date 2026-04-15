from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DBTypeDescriptor:
    canonical_name: str  # e.g. "elasticsearch"
    aliases: list[str]   # e.g. ["elastic", "es", "elasticsearch"]
    display_label: str   # e.g. "Elasticsearch"
    icon_name: str       # maps to a frontend icon key


class DBTypeRegistry:
    """
    Global registry of known database types.

    Registration happens at module import time via `register_db_type()`.
    The `types/` package's __init__.py imports all type modules, guaranteeing
    that every type is registered before any collector runs.

    Adding a new DB type:
        1. Create `app/registry/types/<newtype>.py`
        2. Call `register_db_type(DBTypeDescriptor(...))`
        3. Import it in `app/registry/types/__init__.py`
        — no other files need to change.
    """

    _registry: dict[str, DBTypeDescriptor] = {}  # canonical_name → descriptor
    _alias_map: dict[str, str] = {}               # lowercase alias → canonical_name

    @classmethod
    def register(cls, descriptor: DBTypeDescriptor) -> None:
        cls._registry[descriptor.canonical_name] = descriptor
        for alias in descriptor.aliases:
            cls._alias_map[alias.lower()] = descriptor.canonical_name
        # Also map the canonical name itself (for idempotent resolution)
        cls._alias_map[descriptor.canonical_name.lower()] = descriptor.canonical_name

    @classmethod
    def resolve(cls, raw_name: str) -> str:
        """
        Return the canonical name for `raw_name`, or `"unknown"` if unrecognised.
        Matching is case-insensitive.
        """
        return cls._alias_map.get(raw_name.lower(), "unknown")

    @classmethod
    def get_descriptor(cls, canonical_name: str) -> DBTypeDescriptor | None:
        return cls._registry.get(canonical_name)

    @classmethod
    def all_types(cls) -> list[DBTypeDescriptor]:
        return list(cls._registry.values())


def register_db_type(descriptor: DBTypeDescriptor) -> None:
    """Module-level convenience wrapper for `DBTypeRegistry.register()`."""
    DBTypeRegistry.register(descriptor)
