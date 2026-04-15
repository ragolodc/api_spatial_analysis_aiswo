from typing import Protocol

from .value_objects import Elevation, GeoPoint, GeoPolygon


class ElevationProvider(Protocol):
    def get_highest_point(self, polygon: GeoPolygon) -> tuple[GeoPoint, Elevation]: ...
    def get_point_elevation(self, point: GeoPoint) -> Elevation: ...
