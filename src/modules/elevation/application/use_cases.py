from src.modules.elevation.domain.ports import ElevationProvider
from src.modules.elevation.domain.value_objects import Elevation, GeoPoint, GeoPolygon


class GetHighestPointInPolygon:
    def __init__(self, provider: ElevationProvider) -> None:
        self._provider = provider

    def execute(self, polygon: GeoPolygon) -> tuple[GeoPoint, Elevation]:
        return self._provider.get_highest_point(polygon)


class GetPointElevation:
    def __init__(self, provider: ElevationProvider) -> None:
        self._provider = provider

    def execute(self, point: GeoPoint) -> Elevation:
        return self._provider.get_point_elevation(point)
