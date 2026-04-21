from typing import Protocol
from uuid import UUID

from src.shared.domain.value_objects import GeoPolygon


class ZoneGeometryReader(Protocol):
    def find_polygon(self, zone_id: UUID) -> GeoPolygon | None: ...
