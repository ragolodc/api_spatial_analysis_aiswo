from datetime import datetime, timezone
from uuid import uuid4

from src.main import app
from src.modules.elevation.domain.exceptions import ElevationDataNotFound
from src.modules.elevation.domain.value_objects import Elevation, GeoPoint
from src.modules.elevation.infrastructure.factories import (
    get_get_highest_point,
    get_get_point_elevation,
    get_list_elevation_sources,
    get_zone_geometry_reader,
)
from src.shared.domain import ElevationSource

_API_V1_PREFIX = "/api/v1"


def test_list_elevation_sources_returns_items(client) -> None:
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

    class _ListSources:
        def execute(self):
            return [source]

    app.dependency_overrides[get_list_elevation_sources] = lambda: _ListSources()

    response = client.get(f"{_API_V1_PREFIX}/elevation-sources")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["is_active"] is True


def test_highest_point_by_polygon_returns_feature(client) -> None:
    class _GetHighestPoint:
        def execute(self, polygon):
            return GeoPoint(longitude=-74.1, latitude=4.6), Elevation(meters=2567.3)

    app.dependency_overrides[get_get_highest_point] = lambda: _GetHighestPoint()

    response = client.post(
        f"{_API_V1_PREFIX}/processes/highest-point/execution",
        json={
            "inputs": {
                "polygon": {
                    "type": "Polygon",
                    "coordinates": [[[-74.2, 4.5], [-74.0, 4.5], [-74.0, 4.7], [-74.2, 4.5]]],
                }
            }
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["geometry"]["type"] == "Point"
    assert payload["properties"]["elevation_m"] == 2567.3


def test_highest_point_with_unknown_zone_returns_404(client) -> None:
    class _ZoneReader:
        def find_polygon(self, zone_id):
            return None

    class _UnusedUseCase:
        def execute(self, polygon):
            raise AssertionError("Should not be called")

    app.dependency_overrides[get_get_highest_point] = lambda: _UnusedUseCase()
    app.dependency_overrides[get_zone_geometry_reader] = lambda: _ZoneReader()

    response = client.post(
        f"{_API_V1_PREFIX}/processes/highest-point/execution",
        json={"inputs": {"zone_id": str(uuid4())}},
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Zone not found"


def test_point_elevation_maps_domain_not_found_to_404(client) -> None:
    class _GetPointElevation:
        def execute(self, point):
            raise ElevationDataNotFound("No DEM coverage for point")

    app.dependency_overrides[get_get_point_elevation] = lambda: _GetPointElevation()

    response = client.post(
        f"{_API_V1_PREFIX}/processes/point-elevation/execution",
        json={"inputs": {"point": {"type": "Point", "coordinates": [-74.05, 4.61]}}},
    )

    assert response.status_code == 404
    assert response.json()["message"] == "No DEM coverage for point"


def test_highest_point_requires_polygon_or_zone_id(client) -> None:
    class _Stub:
        def execute(self, *args, **kwargs):
            raise AssertionError("Should not reach use case")

        def find_polygon(self, zone_id):
            return None

    app.dependency_overrides[get_get_highest_point] = lambda: _Stub()
    app.dependency_overrides[get_zone_geometry_reader] = lambda: _Stub()

    response = client.post(
        f"{_API_V1_PREFIX}/processes/highest-point/execution", json={"inputs": {}}
    )

    assert response.status_code == 422
