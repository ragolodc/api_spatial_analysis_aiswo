"""Domain entities for the elevation module."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class ElevationSource:
    """Represents a configured elevation data source."""

    id: UUID
    name: str
    srid: int
    source_url: str | None
    collection: str | None
    resolution_m: float
    is_active: bool
    created_at: datetime
