from datetime import datetime, timezone
from uuid import uuid4

import src.modules.elevation.presentation.processes_router as elevation_processes_router
import src.modules.elevation.presentation.sources_router as elevation_sources_router
from src.modules.elevation.domain.entities import ElevationSource
from src.modules.elevation.domain.exceptions import ElevationDataNotFound
from src.modules.elevation.domain.value_objects import Elevation, GeoPoint

_API_V1_PREFIX = "/api/v1"


def test_list_elevation_sources_returns_items(client, monkeypatch) -> None:
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

    monkeypatch.setattr(
        elevation_sources_router, "get_list_elevation_sources", lambda db: _ListSources()
    )

    response = client.get(f"{_API_V1_PREFIX}/elevation-sources")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["is_active"] is True


def test_highest_point_by_polygon_returns_feature(client, monkeypatch) -> None:
    class _GetHighestPoint:
        def execute(self, polygon):
            return GeoPoint(longitude=-74.1, latitude=4.6), Elevation(meters=2567.3)

    monkeypatch.setattr(
        elevation_processes_router, "get_get_highest_point", lambda db: _GetHighestPoint()
    )

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


def test_highest_point_with_unknown_zone_returns_404(client, monkeypatch) -> None:
    class _ZoneReader:
        def find_polygon(self, zone_id):
            return None

    monkeypatch.setattr(
        elevation_processes_router, "get_zone_geometry_reader", lambda db: _ZoneReader()
    )

    response = client.post(
        f"{_API_V1_PREFIX}/processes/highest-point/execution",
        json={"inputs": {"zone_id": str(uuid4())}},
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Zone not found"


def test_point_elevation_maps_domain_not_found_to_404(client, monkeypatch) -> None:
    class _GetPointElevation:
        def execute(self, point):
            raise ElevationDataNotFound("No DEM coverage for point")

    monkeypatch.setattr(
        elevation_processes_router, "get_get_point_elevation", lambda db: _GetPointElevation()
    )

    response = client.post(
        f"{_API_V1_PREFIX}/processes/point-elevation/execution",
        json={"inputs": {"point": {"type": "Point", "coordinates": [-74.05, 4.61]}}},
    )

    assert response.status_code == 404
    assert response.json()["message"] == "No DEM coverage for point"


def test_highest_point_requires_polygon_or_zone_id(client) -> None:
    response = client.post(
        f"{_API_V1_PREFIX}/processes/highest-point/execution", json={"inputs": {}}
    )

    print(response)

    assert response.status_code == 422
