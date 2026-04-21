"""Shared domain entities used across all bounded contexts."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class ElevationSource:
    """Configured elevation data source. Shared across all bounded contexts that use DEM data."""

    id: UUID
    name: str
    srid: int
    source_url: str | None
    collection: str | None
    resolution_m: float
    is_active: bool
    created_at: datetime
