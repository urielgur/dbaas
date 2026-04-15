from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AbstractCollector(Protocol):
    """Structural protocol shared by GitLabCollector and ArgoCDCollector."""

    async def collect(self) -> object:
        """Run the collection and return results. Concrete type depends on the collector."""
        ...
