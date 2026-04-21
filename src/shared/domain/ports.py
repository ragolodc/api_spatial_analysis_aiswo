from typing import Protocol
from uuid import UUID

from src.shared.domain.entities import ElevationSource
from src.shared.domain.value_objects import GeoPolygon


class ZoneGeometryReader(Protocol):
    def find_polygon(self, zone_id: UUID) -> GeoPolygon | None: ...


class ElevationSourceReader(Protocol):
    """Read-only port for resolving the active elevation source configuration."""

    def find_active(self) -> ElevationSource | None: ...
