# Import all DB type modules here to trigger registration at startup.
# Add one import line per new type file.
from app.registry.types import elasticsearch, mongodb, postgresql

__all__ = ["elasticsearch", "mongodb", "postgresql"]
