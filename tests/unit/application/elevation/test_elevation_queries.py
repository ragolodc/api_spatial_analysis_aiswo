from datetime import datetime, timezone
from uuid import uuid4

from src.modules.elevation.application.queries import (
    GetHighestPointInPolygon,
    GetPointElevation,
    ListElevationSources,
)
from src.modules.elevation.domain.value_objects import Elevation, GeoPoint
from src.shared.domain import ElevationSource, GeoPolygon


class FakeElevationProvider:
    def __init__(self) -> None:
        self.last_polygon = None
        self.last_point = None

    def get_highest_point(self, polygon: GeoPolygon) -> tuple[GeoPoint, Elevation]:
        self.last_polygon = polygon
        return GeoPoint(longitude=-74.1, latitude=4.6), Elevation(meters=2567.3)

    def get_point_elevation(self, point: GeoPoint) -> Elevation:
        self.last_point = point
        return Elevation(meters=2710.0)


class FakeElevationSourceRepository:
    def __init__(self, items: list[ElevationSource]) -> None:
        self._items = items

    def find_all(self):
        return list(self._items)

    def find_active(self):
        return next((item for item in self._items if item.is_active), None)


def test_get_highest_point_delegates_to_provider() -> None:
    provider = FakeElevationProvider()
    polygon = GeoPolygon(coordinates=[[[-74.2, 4.5], [-74.0, 4.5], [-74.0, 4.7], [-74.2, 4.5]]])

    point, elevation = GetHighestPointInPolygon(provider).execute(polygon)

    assert provider.last_polygon == polygon
    assert point.longitude == -74.1
    assert point.latitude == 4.6
    assert elevation.meters == 2567.3


def test_get_point_elevation_delegates_to_provider() -> None:
    provider = FakeElevationProvider()
    point = GeoPoint(longitude=-74.05, latitude=4.61)

    elevation = GetPointElevation(provider).execute(point)

    assert provider.last_point == point
    assert elevation.meters == 2710.0


def test_list_elevation_sources_returns_repository_items() -> None:
    source = ElevationSource(
        id=uuid4(),
        name="planetary_computer",
        srid=4326,
        source_url="https://planetarycomputer.microsoft.com/api/stac/v1",
        collection="cop-dem-glo-30",
        resolution_m=30.0,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    repo = FakeElevationSourceRepository(items=[source])

    result = ListElevationSources(repo).execute()

    assert len(result) == 1
    assert result[0].name == "planetary_computer"
    assert result[0].is_active is True
