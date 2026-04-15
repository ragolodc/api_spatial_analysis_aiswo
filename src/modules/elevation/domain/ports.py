from typing import Protocol
from uuid import UUID

from src.modules.elevation.domain.entities import ElevationSource
from src.modules.elevation.domain.value_objects import Elevation, GeoPoint
from src.shared.domain import GeoPolygon


class ElevationProvider(Protocol):
    def get_highest_point(self, polygon: GeoPolygon) -> tuple[GeoPoint, Elevation]: ...
    def get_point_elevation(self, point: GeoPoint) -> Elevation: ...


class ElevationSourceRepository(Protocol):
    def find_all(self) -> list[ElevationSource]: ...
    def find_active(self) -> ElevationSource | None: ...


class ZoneGeometryReader(Protocol):
    """Narrow read port: get zone geometry without coupling to the zones module."""

    def find_polygon(self, zone_id: UUID) -> GeoPolygon | None: ...
