"""Query: Get point elevation."""

from src.modules.elevation.domain.ports import ElevationProvider
from src.modules.elevation.domain.value_objects import Elevation, GeoPoint


class GetPointElevation:
    """Query use case to retrieve the elevation at a specific point."""

    def __init__(self, provider: ElevationProvider) -> None:
        self._provider = provider

    def execute(self, point: GeoPoint) -> Elevation:
        return self._provider.get_point_elevation(point)
