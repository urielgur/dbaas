from __future__ import annotations

import app.registry.types  # noqa: F401 — triggers registration
from app.registry.db_type_registry import DBTypeRegistry


def test_resolve_canonical():
    assert DBTypeRegistry.resolve("postgresql") == "postgresql"


def test_resolve_alias():
    assert DBTypeRegistry.resolve("postgres") == "postgresql"
    assert DBTypeRegistry.resolve("es") == "elasticsearch"
    assert DBTypeRegistry.resolve("mongo") == "mongodb"


def test_resolve_case_insensitive():
    assert DBTypeRegistry.resolve("PostgreSQL") == "postgresql"
    assert DBTypeRegistry.resolve("ELASTIC") == "elasticsearch"


def test_resolve_unknown():
    assert DBTypeRegistry.resolve("cassandra") == "unknown"


def test_get_descriptor():
    d = DBTypeRegistry.get_descriptor("elasticsearch")
    assert d is not None
    assert d.display_label == "Elasticsearch"


def test_all_types():
    types = DBTypeRegistry.all_types()
    canonical_names = {d.canonical_name for d in types}
    assert {"elasticsearch", "mongodb", "postgresql"}.issubset(canonical_names)
