from datetime import datetime, timezone
from uuid import uuid4

from src.main import app
from src.modules.zones.domain.entities import Zone, ZoneType
from src.modules.zones.infrastructure.factories import get_create_zone, get_get_zone, get_list_zones
from src.shared.domain import GeoPolygon

_API_V1_PREFIX = "/api/v1"


def _sample_zone() -> Zone:
    return Zone(
        id=uuid4(),
        name="North field",
        zone_type=ZoneType.FARM_BOUNDARY,
        geometry=GeoPolygon(coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]]),
        created_at=datetime.now(timezone.utc),
    )


def test_list_zones_returns_feature_collection(client) -> None:
    zone = _sample_zone()

    class _ListZones:
        def execute(self):
            return [zone]

    app.dependency_overrides[get_list_zones] = lambda: _ListZones()

    response = client.get(f"{_API_V1_PREFIX}/collections/zones/items")

    assert response.status_code == 200
    payload = response.json()
    assert payload["number_matched"] == 1
    assert payload["features"][0]["properties"]["name"] == "North field"


def test_get_zone_returns_404_when_not_found(client) -> None:
    class _GetZone:
        def execute(self, zone_id):
            return None

    app.dependency_overrides[get_get_zone] = lambda: _GetZone()

    response = client.get(f"{_API_V1_PREFIX}/collections/zones/items/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["message"] == "Zone not found"


def test_create_zone_returns_created_feature(client) -> None:
    zone = _sample_zone()

    class _CreateZone:
        def execute(self, name, zone_type, geometry):
            assert name == "North field"
            assert zone_type == ZoneType.FARM_BOUNDARY
            assert geometry.coordinates[0][0] == [0.0, 0.0]
            return zone

    app.dependency_overrides[get_create_zone] = lambda: _CreateZone()

    response = client.post(
        f"{_API_V1_PREFIX}/collections/zones/items",
        json={
            "name": "North field",
            "zone_type": "farm_boundary",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]],
            },
        },
    )

    assert response.status_code == 201
    assert response.json()["properties"]["zone_type"] == "farm_boundary"
