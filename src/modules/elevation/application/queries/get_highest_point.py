"""Query: Get highest point in polygon."""

from src.modules.elevation.domain.ports import ElevationProvider
from src.modules.elevation.domain.value_objects import Elevation, GeoPoint, GeoPolygon


class GetHighestPointInPolygon:
    """Query use case to retrieve the highest elevation point within a polygon."""

    def __init__(self, provider: ElevationProvider) -> None:
        self._provider = provider

    def execute(self, polygon: GeoPolygon) -> tuple[GeoPoint, Elevation]:
        return self._provider.get_highest_point(polygon)
